# FinBee user and data guide

[Back to README](../README.md)

These steps describe source behavior. See [SETUP.md](SETUP.md) for environment preparation and the recorded verification scope.

## Basic workflow

1. Register and sign in. Registration seeds default categories for the new user.
2. Add an account and opening balance.
3. Record a transaction with account, date, positive amount, category, and type: income, expense, or investment.
4. Review transactions and use the edit/delete actions when appropriate.
5. Inspect Dashboard and Insights for trends and totals.
6. Use Profile for personal details and the data backup/restore page.

Source validation rejects future transaction dates and unsupported transaction types.

## Totals

Account balance is opening balance + income - expense - investment.

The Insights helper subtracts investments when calculating savings, while Dashboard weekly/monthly savings use income - expense. These definitions differ in the current source; do not assume the two displays mean the same thing.

## Export and restore

| Route | Purpose |
| --- | --- |
| /export/transactions | Download transaction CSV |
| /export/data | Download JSON financial backup |
| /import/data | Upload a FinBee JSON backup |

Use these while logged in. CSV columns are Date, Type, Category, Account, Amount, and Note. The CSV writer concatenates fields directly, so commas/newlines in text can affect parsing.

JSON includes user name/email/export timestamp, accounts, categories, and transactions. It does **not** include login-password hashes or uploaded profile-image files, and import does not recreate the user account. Sign in to the intended destination account first.

### Import matching rules

- Accounts match by current user and account name; existing account details are not overwritten.
- Categories match by current user, name, and type.
- Transactions are considered duplicates by current user, date, amount, and transaction type.
- Account, category, and note are **not** part of the transaction duplicate check. Two legitimate transactions with the same date/amount/type can therefore be collapsed.
- Name-based category lookup during transaction import can be ambiguous when category names are reused across types.
- Source IDs and creation timestamps are not a full identity-preserving database restore.

Export before importing, try a disposable account first, and compare counts/totals afterwards. Keep backup files private: they contain personal financial data and contact information.

For a complete local archive, stop the application and preserve the database plus user_content/ together. This is distinct from JSON import and should be restored into a separate test copy before replacing valuable data.

## Architecture

Flask routes and business logic live in app.py. SQLAlchemy entities live in models.py:

- User owns accounts, categories, and transactions.
- Account contains opening balance and active status.
- Category combines a name and income/expense/investment type.
- Transaction links a user, account, category, amount, date, and optional note.

HTML files are Flask templates, not independent working pages. finbee_desktop.py wraps the same Flask app in a local desktop window.

## Validation still needed

No UI screenshots, complete acceptance-test report, or verified release are included. A future validation should cover registration, separate-user isolation, transaction edits, all three transaction types, JSON round-trip including same-day equal amounts, CSV special characters, and desktop persistence after restart.

The historical UI report describes an earlier layout and includes success claims that have not been revalidated against this checkout.
