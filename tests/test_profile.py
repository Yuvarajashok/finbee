# test_profile.py
from tests.init_test_db import create_test_user
from io import BytesIO

def login(client):
    client.post("/login", data={
        "email": "test@finbee.com",
        "password": "password123"
    }, follow_redirects=True)


def test_profile_update(client, app):
    with app.app_context():
        create_test_user()

    login(client)

    data = {
        "name": "Updated User",
        "photo": (BytesIO(b"fake image data"), "test.png")
    }

    res = client.post("/profile", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert b"Updated User" in res.data
