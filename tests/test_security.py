# test_security.py
def test_protected_routes_redirect(client):
    protected_routes = [
        "/",
        "/accounts",
        "/transactions",
        "/dashboard",
        "/profile"
    ]

    for route in protected_routes:
        res = client.get(route)
        assert res.status_code in (301, 302)
