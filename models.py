from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ==============================
# USER
# ==============================
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✅ Profile picture filename
    profile_pic = db.Column(db.String(200), default="default.jpg")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    accounts = db.relationship("Account", backref="user", lazy=True)
    categories = db.relationship("Category", backref="user", lazy=True)
    transactions = db.relationship("Transaction", backref="user", lazy=True)

# ==============================
# ACCOUNT
# ==============================
class Account(db.Model):
    __tablename__ = "account"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    opening_balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "account_name", name="uq_user_account"),
    )

    transactions = db.relationship("Transaction", backref="account", lazy=True)


# ==============================
# CATEGORY
# ==============================
class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # income / expense / investment

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "name", "type", name="uq_user_category"),
    )

    transactions = db.relationship("Transaction", backref="category", lazy=True)


# ==============================
# TRANSACTION
# ==============================
class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
