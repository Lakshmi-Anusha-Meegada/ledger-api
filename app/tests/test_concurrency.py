import threading
from fastapi.testclient import TestClient
from app.main import app
import time
client = TestClient(app)
def make_transfer(src, dst, amount):
    resp = client.post("/transfers", json={
        "type": "transfer",
        "amount": f"{amount:.2f}",
        "currency": "USD",
        "source_account_id": src,
        "destination_account_id": dst,
        "description": "concurrent transfer"
    })
    return resp
def test_concurrent_transfers_no_negative_balance():
    # create a funding account and two recipients
    r = client.post("/accounts", json={"user_id":"c_fund","account_type":"checking","currency":"USD"})
    fund = r.json()
    r = client.post("/accounts", json={"user_id":"c_a","account_type":"savings","currency":"USD"})
    a = r.json()
    r = client.post("/accounts", json={"user_id":"c_b","account_type":"savings","currency":"USD"})
    b = r.json()
    # deposit 100 into fund
    r = client.post("/deposits", json={
        "type":"deposit","amount":"100.00","currency":"USD","destination_account_id":fund["id"], "description":"funding"
    })
    assert r.status_code in (200,201)
    # start N concurrent transfers of 30 each (total 90) and one more that would cause overdraft if race occurs
    results = []
    def worker(amount):
        resp = make_transfer(fund["id"], a["id"], amount)
        results.append(resp)
    threads = []
    for _ in range(3):
        t = threading.Thread(target=worker, args=(30.00,))
        threads.append(t)
        t.start()
    # a small concurrent additional transfer that should fail if balance enforcement works
    t_extra = threading.Thread(target=worker, args=(30.00,))
    threads.append(t_extra)
    t_extra.start()
    for t in threads:
        t.join()
    # gather statuses
    statuses = [r.status_code for r in results]
    successes = [s for s in statuses if s in (200,201)]
    failures = [s for s in statuses if s not in (200,201)]
    # At least three should succeed (90 total) and the extra one should be rejected or rolled back to prevent negative balance
    assert len(successes) >= 3
    # verify fund balance is never negative
    r = client.get(f"/accounts/{fund['id']}")
    assert r.status_code == 200
    bal = float(r.json()["balance"])
    assert bal >= 0.0
