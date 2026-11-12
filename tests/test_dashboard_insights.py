# test_dashboard_insights.py
from tests.init_test_db import create_test_user

def login(client):
    client.post("/login", data={
        "email": "test@finbee.com",
        "password": "password123"
    }, follow_redirects=True)


def test_dashboard_access(client, app):
    with app.app_context():
        create_test_user()

    login(client)

    res = client.get("/dashboard")
    assert res.status_code == 200


def test_insights_access(client, app):
    with app.app_context():
        create_test_user()

    login(client)

    res = client.get("/insights")
    assert res.status_code == 200
