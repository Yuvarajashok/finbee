from models import db, Account, Transaction
from datetime import date


def test_account_balance_logic(app):
    with app.app_context():
        acc = Account(
            user_id=1,
            account_name="cash",
            opening_balance=1000
        )
        db.session.add(acc)
        db.session.commit()

        t1 = Transaction(
            user_id=1,
            account_id=acc.id,
            category_id=1,
            date=date.today(),
            amount=500,
            transaction_type="income"
        )

        t2 = Transaction(
            user_id=1,
            account_id=acc.id,
            category_id=1,
            date=date.today(),
            amount=200,
            transaction_type="expense"
        )

        db.session.add_all([t1, t2])
        db.session.commit()

        balance = acc.opening_balance + 500 - 200
        assert balance == 1300
