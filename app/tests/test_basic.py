from fastapi.testclient import TestClient
from app.main import app
import decimal
client = TestClient(app)
def test_create_accounts_and_basic_flow():
    # create two accounts
    r = client.post("/accounts", json={"user_id": "test_alice", "account_type": "checking", "currency": "USD"})
    assert r.status_code == 201
    a1 = r.json()
    r = client.post("/accounts", json={"user_id": "test_bob", "account_type": "savings", "currency": "USD"})
    assert r.status_code == 201
    a2 = r.json()
    # deposit to alice
    r = client.post("/deposits", json={
        "type": "deposit",
        "amount": "200.00",
        "currency": "USD",
        "destination_account_id": a1["id"],
        "description": "test deposit"
    })
    assert r.status_code == 200 or r.status_code == 201
    tx_deposit = r.json()
    assert float(tx_deposit["amount"]) == 200.0
    assert tx_deposit["status"] in ("completed", "pending")
    # check alice balance
    r = client.get(f"/accounts/{a1['id']}")
    assert r.status_code == 200
    bal_a1 = r.json()["balance"]
    assert float(bal_a1) >= 200.0
    # transfer from alice -> bob
    r = client.post("/transfers", json={
        "type": "transfer",
        "amount": "50.00",
        "currency": "USD",
        "source_account_id": a1["id"],
        "destination_account_id": a2["id"],
        "description": "test transfer"
    })
    assert r.status_code == 200 or r.status_code == 201
    tx_transfer = r.json()
    assert float(tx_transfer["amount"]) == 50.0
    assert tx_transfer["status"] in ("completed", "pending")
    # verify balances update correctly
    r = client.get(f"/accounts/{a1['id']}")
    a1_after = r.json()
    r = client.get(f"/accounts/{a2['id']}")
    a2_after = r.json()
    assert float(a1_after["balance"]) == float(bal_a1) - 50.0
    assert float(a2_after["balance"]) >= 50.0
    # ledger should contain entries
    r = client.get(f"/accounts/{a1['id']}/ledger")
    assert r.status_code == 200
    ledger_a1 = r.json()
    assert any(e["entry_type"] in ("debit", "credit") for e in ledger_a1)
