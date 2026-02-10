from flask import Flask, render_template, request, redirect, url_for, Response, send_from_directory
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Account, Category, Transaction
from datetime import datetime, date, timedelta
from sqlalchemy import func
import os
import csv
import sys




# ---------------- APP SETUP ----------------
app = Flask(__name__)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure persistent directories exist
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
USER_CONTENT_DIR = os.path.join(BASE_DIR, 'user_content')
os.makedirs(USER_CONTENT_DIR, exist_ok=True)

app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
    BASE_DIR, 'instance', 'finance.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
     return db.session.get(User, int(user_id)) 


TXN_TYPES = ('income', 'expense', 'investment')


# ---------------- SEED CATEGORIES ----------------

# Seed default categories for a specific user
def seed_categories(user_id):
    if Category.query.filter_by(user_id=user_id).first():
        return
    defaults = [
        ('part-time work', 'income'),
        ('online income', 'income'),
        ('scholarship', 'income'),
        ('food', 'expense'),
        ('transport', 'expense'),
        ('education', 'expense'),
        ('family', 'expense'),
        ('personal', 'expense'),
        ('emergency', 'expense'),
    ]
    for name, ctype in defaults:
        db.session.add(Category(user_id=user_id, name=name, type=ctype))
    db.session.commit()


with app.app_context():
    db.create_all()


# ---------------- HELPERS ----------------
def normalize(text):
    return text.strip().lower()


def get_account_balance(account_id):
    inc = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id,
        account_id=account_id,
        transaction_type='income'
    ).scalar() or 0.0

    exp = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id,
        account_id=account_id,
        transaction_type='expense'
    ).scalar() or 0.0

    inv = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id,
        account_id=account_id,
        transaction_type='investment'
    ).scalar() or 0.0

    acc = db.session.get(Account, account_id)
    if not acc:
        return 0.0
    return (acc.opening_balance or 0.0) + inc - exp - inv


def get_totals(start, end):
    rows = db.session.query(
        Transaction.transaction_type,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.date.between(start, end)
    ).group_by(Transaction.transaction_type).all()

    data = {'income': 0.0, 'expense': 0.0, 'investment': 0.0}
    for t, amt in rows:
        if t in data:
            data[t] = float(amt or 0.0)

    savings = data['income'] - data['expense'] - data['investment']
    return data, savings


# ---------------- HOME ----------------
@app.route('/')
@login_required
def index():
    return render_template('home.html')


# ---------------- AUTH ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email'].lower()).first():
            return render_template("register.html", error="User already exists")

        user = User(
            name=request.form['name'].strip(),
            email=request.form['email'].strip().lower(),
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        # Seed default categories for this user
        seed_categories(user.id)
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'].strip().lower()).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        error = "Invalid email or password"

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------------- ACCOUNTS ----------------
@app.route('/accounts', methods=['GET', 'POST'])
@login_required
def accounts():
    error = None

    if request.method == 'POST':
        name = normalize(request.form['account_name'])
        opening = float(request.form['opening_balance'])

        if opening < 0:
            error = "Opening balance cannot be negative"

        if not error:
            acc = Account.query.filter_by(
                user_id=current_user.id,
                account_name=name
            ).first()

            if acc:
                acc.opening_balance = opening
            else:
                acc = Account(
                    user_id=current_user.id,
                    account_name=name,
                    opening_balance=opening
                )
                db.session.add(acc)

            db.session.commit()
            return redirect(url_for('accounts'))

    accounts = Account.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()

    return render_template('accounts.html', accounts=accounts, error=error)


@app.route('/accounts/delete/<int:acc_id>')
@login_required
def delete_account(acc_id):
    acc = Account.query.filter_by(
        id=acc_id,
        user_id=current_user.id
    ).first_or_404()

    if Transaction.query.filter_by(account_id=acc.id).first():
        return redirect(url_for('accounts'))

    db.session.delete(acc)
    db.session.commit()
    return redirect(url_for('accounts'))


# ---------------- TRANSACTIONS ----------------
@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    error = None

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    txns = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
        except ValueError:
            error = "Invalid amount"

        if not error and amount <= 0:
            error = "Amount must be greater than zero"

        txn_date = datetime.strptime(request.form['txn_date'], '%Y-%m-%d').date()
        if not error and txn_date > date.today():
            error = "Future date not allowed"

        txn_type = request.form['transaction_type']
        if not error and txn_type not in TXN_TYPES:
            error = "Invalid transaction type"

        cat_name = normalize(request.form['category_name'])
        if not error and not cat_name:
            error = "Category is required"

        if error:
            return render_template(
                'transactions.html',
                accounts=accounts,
                transactions=txns,
                today=date.today(),
                error=error
            )


        category = Category.query.filter_by(
            user_id=current_user.id,
            name=cat_name,
            type=txn_type
        ).first()

        if not category:
            category = Category(
                user_id=current_user.id,
                name=cat_name,
                type=txn_type
            )
            db.session.add(category)
            db.session.commit()

        txn = Transaction(
            user_id=current_user.id,
            date=txn_date,
            amount=amount,
            transaction_type=txn_type,
            category_id=category.id,
            account_id=int(request.form['account_id']),
            note=request.form.get('note')
        )

        db.session.add(txn)
        db.session.commit()
        return redirect(url_for('transactions'))

    return render_template(
        'transactions.html',
        accounts=accounts,
        transactions=txns,
        today=date.today(),
        error=error
    )


@app.route('/transactions/delete/<int:txn_id>')
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.filter_by(
        id=txn_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(txn)
    db.session.commit()
    return redirect(url_for('transactions'))
# ---------------- INSIGHTS ----------------
@app.route('/insights')
@login_required
def insights():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    weekly, weekly_savings = get_totals(
        week_start, week_start + timedelta(days=6)
    )
    monthly, monthly_savings = get_totals(month_start, today)

    balances = {
        acc.account_name: get_account_balance(acc.id)
        for acc in Account.query.filter_by(user_id=current_user.id).all()
    }

    grand_total = sum(balances.values())

    return render_template(
        'insights.html',
        weekly=weekly,
        weekly_savings=weekly_savings,
        monthly=monthly,
        monthly_savings=monthly_savings,
        balances=balances,
        grand_total=grand_total
    )
# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    weekly_income = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'income',
        Transaction.date >= week_start
    ).scalar()

    weekly_expense = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.date >= week_start
    ).scalar()

    monthly_income = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'income',
        Transaction.date >= month_start
    ).scalar()

    monthly_expense = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.date >= month_start
    ).scalar()

    # ---- Monthly trend ----
    month_col = func.strftime('%Y-%m', Transaction.date)

    rows = db.session.query(
        month_col,
        Transaction.transaction_type,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id
    ).group_by(month_col, Transaction.transaction_type).order_by(month_col).all()

    trend = {}
    for m, t, a in rows:
        trend.setdefault(m, {'income': 0.0, 'expense': 0.0})
        trend[m][t] = float(a)

    months = list(trend.keys())
    income = [trend[m]['income'] for m in months]
    expense = [trend[m]['expense'] for m in months]
    savings = [trend[m]['income'] - trend[m]['expense'] for m in months]

    income_pie = [
        {"category": n, "amount": float(a)}
        for n, a in db.session.query(
            Category.name, func.sum(Transaction.amount)
        )
        .join(Category)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'income'
        )
        .group_by(Category.name)
        .all()
    ]

    expense_pie = [
        {"category": n, "amount": float(a)}
        for n, a in db.session.query(
            Category.name, func.sum(Transaction.amount)
        )
        .join(Category)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense'
        )
        .group_by(Category.name)
        .all()
    ]

    empty = not Transaction.query.filter_by(
        user_id=current_user.id
    ).first()

    return render_template(
        'dashboard.html',
        weekly_income=weekly_income,
        weekly_expense=weekly_expense,
        weekly_savings=weekly_income - weekly_expense,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        monthly_savings=monthly_income - monthly_expense,
        months=months,
        income=income,
        expense=expense,
        savings=savings,
        income_pie=income_pie,
        expense_pie=expense_pie,
        empty=empty
    )



# ---------------- EXPORT ----------------
@app.route('/export/transactions')
@login_required
def export_transactions():
    rows = (
        db.session.query(
            Transaction.date,
            Transaction.transaction_type,
            Category.name,
            Account.account_name,
            Transaction.amount,
            Transaction.note
        )
        .join(Category)
        .join(Account)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date)
        .all()
    )

    def generate():
        yield "Date,Type,Category,Account,Amount,Note\n"
        for r in rows:
            yield f"{r[0].strftime('%Y-%m-%d')},{r[1]},{r[2]},{r[3]},{r[4]},{r[5] or ''}\n"

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=finance_transactions.csv'}
    )


# ---------------- PROFILE ----------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required

def profile():
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            error = "Name cannot be empty"
        else:
            current_user.name = name

        file = request.files.get('photo')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                error = "Only JPG or PNG images allowed"
            else:
                import time
                timestamp = int(time.time())
                filename = f"user_{current_user.id}_{timestamp}.{ext}"
                file.save(os.path.join(USER_CONTENT_DIR, filename))
                
                # Optional: clean up old file if it's not default and different
                if current_user.profile_pic and not current_user.profile_pic.startswith('default'):
                    old_path = os.path.join(USER_CONTENT_DIR, current_user.profile_pic)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass # Ignore cleanup errors

                current_user.profile_pic = filename

        if not error:
            db.session.commit()
            return redirect(url_for('profile'))

    return render_template('profile.html', error=error)


@app.route('/user_content/<filename>')
def uploaded_file(filename):
    return send_from_directory(USER_CONTENT_DIR, filename)



# ---------------- DATA EXPORT/IMPORT ----------------
import json

@app.route('/export/data')
@login_required
def export_data():
    """Export all user data as JSON"""
    # Get all user data
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    # Serialize data
    data = {
        'user': {
            'name': current_user.name,
            'email': current_user.email,
            'exported_at': datetime.now().isoformat()
        },
        'accounts': [
            {
                'id': acc.id,
                'account_name': acc.account_name,
                'opening_balance': acc.opening_balance,
                'is_active': acc.is_active,
                'created_at': acc.created_at.isoformat()
            }
            for acc in accounts
        ],
        'categories': [
            {
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'created_at': cat.created_at.isoformat()
            }
            for cat in categories
        ],
        'transactions': [
            {
                'id': txn.id,
                'date': txn.date.isoformat(),
                'amount': txn.amount,
                'transaction_type': txn.transaction_type,
                'category_name': txn.category.name,
                'account_name': txn.account.account_name,
                'note': txn.note,
                'created_at': txn.created_at.isoformat()
            }
            for txn in transactions
        ]
    }
    
    # Return as downloadable JSON file
    filename = f"finbee_export_{current_user.id}_{date.today().isoformat()}.json"
    return Response(
        json.dumps(data, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@app.route('/import/data', methods=['GET', 'POST'])
@login_required
def import_data():
    """Import user data from JSON file"""
    error = None
    success = False
    
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                error = "No file selected"
            else:
                file = request.files['file']
                if file.filename == '':
                    error = "No file selected"
                elif not file.filename.endswith('.json'):
                    error = "Only JSON files are allowed"
                else:
                    # Read and parse JSON
                    content = file.read().decode('utf-8')
                    data = json.loads(content)
                    
                    # Validate structure
                    if 'accounts' not in data or 'categories' not in data or 'transactions' not in data:
                        error = "Invalid file format"
                    else:
                        # Import accounts
                        account_map = {}  # Map old IDs to new IDs
                        for acc_data in data['accounts']:
                            existing = Account.query.filter_by(
                                user_id=current_user.id,
                                account_name=acc_data['account_name']
                            ).first()
                            
                            if not existing:
                                acc = Account(
                                    user_id=current_user.id,
                                    account_name=acc_data['account_name'],
                                    opening_balance=acc_data.get('opening_balance', 0.0),
                                    is_active=acc_data.get('is_active', True)
                                )
                                db.session.add(acc)
                                db.session.flush()
                                account_map[acc_data['id']] = acc.id
                            else:
                                account_map[acc_data['id']] = existing.id
                        
                        # Import categories
                        category_map = {}  # Map old IDs to new IDs
                        for cat_data in data['categories']:
                            existing = Category.query.filter_by(
                                user_id=current_user.id,
                                name=cat_data['name'],
                                type=cat_data['type']
                            ).first()
                            
                            if not existing:
                                cat = Category(
                                    user_id=current_user.id,
                                    name=cat_data['name'],
                                    type=cat_data['type']
                                )
                                db.session.add(cat)
                                db.session.flush()
                                category_map[cat_data['id']] = cat.id
                            else:
                                category_map[cat_data['id']] = existing.id
                        
                        # Import transactions
                        imported_count = 0
                        for txn_data in data['transactions']:
                            # Check if transaction already exists (by date, amount, type)
                            existing = Transaction.query.filter_by(
                                user_id=current_user.id,
                                date=datetime.strptime(txn_data['date'], '%Y-%m-%d').date(),
                                amount=txn_data['amount'],
                                transaction_type=txn_data['transaction_type']
                            ).first()
                            
                            if not existing:
                                old_account_id = txn_data.get('account_id') or [acc['id'] for acc in data['accounts'] if acc['account_name'] == txn_data['account_name']][0]
                                old_category_id = txn_data.get('category_id') or [cat['id'] for cat in data['categories'] if cat['name'] == txn_data['category_name']][0]
                                
                                new_account_id = account_map.get(old_account_id)
                                new_category_id = category_map.get(old_category_id)
                                
                                if new_account_id and new_category_id:
                                    txn = Transaction(
                                        user_id=current_user.id,
                                        account_id=new_account_id,
                                        category_id=new_category_id,
                                        date=datetime.strptime(txn_data['date'], '%Y-%m-%d').date(),
                                        amount=txn_data['amount'],
                                        transaction_type=txn_data['transaction_type'],
                                        note=txn_data.get('note')
                                    )
                                    db.session.add(txn)
                                    imported_count += 1
                        
                        db.session.commit()
                        success = True
                        return render_template(
                            'import_data.html',
                            success=True,
                            message=f"Successfully imported {imported_count} transactions!"
                        )
        
        except json.JSONDecodeError:
            error = "Invalid JSON file"
        except Exception as e:
            db.session.rollback()
            error = f"Import failed: {str(e)}"
    
    return render_template('import_data.html', error=error, success=success)


# ---------------- RUN ----------------
if __name__ == '__main__':
    # For direct Flask execution only (not used in desktop.py)
    # Desktop app uses desktop.py as entry point
    if os.environ.get('FLASK_ENV') == 'production':
        print("[WARNING] Do not run app.py directly in production. Use a WSGI server or the desktop entry point.")
    port = os.environ.get('FLASK_PORT', 5000)
    app.run(debug=True, port=int(port))
