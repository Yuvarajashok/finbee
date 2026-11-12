from models import db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    user = User(
        name="Test User",
        email="test@finbee.com",
        password=generate_password_hash("password123")
    )
    db.session.add(user)
    db.session.commit()
    return user
