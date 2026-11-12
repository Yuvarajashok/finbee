# test_accounts.py
from tests.init_test_db import create_test_user

def login(client):
    return client.post("/login", data={
        "email": "test@finbee.com",
        "password": "password123"
    }, follow_redirects=True)


def test_add_account(client, app):
    with app.app_context():
        create_test_user()

    login(client)

    res = client.post("/accounts", data={
        "account_name": "cash",
        "opening_balance": "5000"
    }, follow_redirects=True)

    assert b"cash" in res.data
