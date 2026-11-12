# test_transactions.py
from tests.init_test_db import create_test_user
from models import db, Account

def login(client):
    client.post("/login", data={
        "email": "test@finbee.com",
        "password": "password123"
    }, follow_redirects=True)


def test_add_transaction(client, app):
    with app.app_context():
        user = create_test_user()
        acc = Account(user_id=user.id, account_name="cash", opening_balance=1000)
        db.session.add(acc)
        db.session.commit()

    login(client)

    res = client.post("/transactions", data={
        "txn_date": "2024-01-01",
        "amount": "200",
        "transaction_type": "expense",
        "category_name": "food",
        "account_id": "1",
        "note": "lunch"
    }, follow_redirects=True)

    assert b"food" in res.data
