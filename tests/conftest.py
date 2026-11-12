import sys
import os
import pytest
from werkzeug.security import generate_password_hash

# 🔥 ADD PROJECT ROOT TO PYTHON PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from models import db, User


@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
    })

    with flask_app.app_context():
        db.create_all()

        user = User(
            id=1,
            name="Test User",
            email="test@example.com",
            password=generate_password_hash("password"),
        )
        db.session.add(user)
        db.session.commit()

        yield flask_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post("/login", data={
        "email": "test@example.com",
        "password": "password"
    })
    return client
