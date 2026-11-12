import sys, os, pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

def test_home_redirect(client):
    res = client.get("/")
    assert res.status_code in (200, 302)

def test_dashboard_access(logged_in_client):
    res = logged_in_client.get("/dashboard")
    assert res.status_code == 200

def test_transaction_route_exists(logged_in_client):
    res = logged_in_client.get("/transactions")
    assert res.status_code == 200
