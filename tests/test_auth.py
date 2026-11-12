# test_auth.py
from tests.init_test_db import create_test_user

def test_register(client):
    res = client.post("/register", data={
        "name": "User One",
        "email": "user1@finbee.com",
        "password": "secret123"
    }, follow_redirects=True)

    assert b"Login" in res.data


def test_login_logout(client, app):
    with app.app_context():
        create_test_user()

    res = client.post("/login", data={
        "email": "test@finbee.com",
        "password": "password123"
    }, follow_redirects=True)

    assert b"Welcome" in res.data

    res = client.get("/logout", follow_redirects=True)
    assert b"Login" in res.data
