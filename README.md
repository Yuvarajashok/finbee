# FinBee

An academic personal-finance tracking application built with Python, Flask, SQLAlchemy/SQLite, HTML templates, and an optional pywebview desktop window.

## Features in the source

- Register/login and user-specific financial records.
- Accounts with opening balances.
- Income, expense, and investment transactions with categories.
- Dashboard and insights views.
- CSV transaction export and JSON financial-data backup/import.
- Profile details and image uploads.
- Desktop launcher using Waitress and pywebview; PyInstaller build specification.

## Current checkout status

The original templates, styles, generic icons/avatar, tests, and transaction-edit route have been restored from the local project. Existing root HTML copies remain for compatibility; Flask uses templates/.

Private databases, user images, uploads, logs, virtual environments, and build outputs are excluded. See setup for runtime and test limitations.

## Documentation

- [Setup, launch modes, storage, and desktop build](docs/SETUP.md)
- [User guide, backups, architecture, and limitations](docs/USER_GUIDE.md)
- [Contributing](CONTRIBUTING.md)
- [Historical UI redesign report](UI_REDESIGN_REPORT.txt)

The historical report's production-readiness and successful-testing statements are not fresh verification. The restored templates/ and static/ folders now match those references, but this does not revalidate every claim in the report.

## Project notes

The original project was created to practice Python, data handling, and application development. This documentation update is based on source inspection, with isolated smoke checks described in the setup guide; desktop packaging is not verified. No verified screenshots or hosted demo are supplied. No license file is present; this update does not choose one.
