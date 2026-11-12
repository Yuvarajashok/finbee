# FinBee setup and operation

[Back to README](../README.md)

## Prerequisites

The restored local source includes templates/, static/ assets, and tests/. Root HTML copies are retained; the runtime uses templates/. Private data was not copied.

Use an isolated Python environment. The recovered environment metadata names Python 3.10.11, but its interpreter is absent. requirements.txt records web dependency versions used in the smoke check; requirements-desktop.txt adds unpinned optional desktop/build packages. This is not a complete historical environment lock file.

## Prepare an isolated environment

```powershell
git clone https://github.com/Yuvarajashok/finbee.git
cd finbee
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Web dependencies were selected from imports and pinned to the smoke-check environment. Transitive dependencies and optional desktop packages are not fully locked.

## Web mode

From the repository root:

```powershell
.\.venv\Scripts\python.exe app.py
```

The source defaults to port 5000, configurable through FLASK_PORT. Visit http://127.0.0.1:5000 with the default setting. Direct execution enables Flask debug mode; it is a local-development entry point.

## Desktop mode

First install optional dependencies with `python -m pip install -r requirements-desktop.txt` in the activated environment.

```powershell
.\.venv\Scripts\python.exe finbee_desktop.py
```

The launcher chooses a free local port, starts Waitress on 127.0.0.1, and opens a pywebview window. On Windows it explicitly requests the Edge Chromium renderer; its runtime must be available. Other operating systems and desktop runtime compatibility have not been verified here.

## Database and configuration

app.py sets configuration directly. It does not load config.py.

- Source mode: BASE_DIR is the directory containing app.py.
- Frozen executable mode: BASE_DIR is the executable's directory.
- Database: BASE_DIR/instance/finance.db.
- Uploaded profile images: BASE_DIR/user_content/.
- Directories and missing database tables are created during application initialization.
- The source uses a development secret key; a public deployment requires separately authorized implementation/configuration work.

Database entities are users, accounts, categories, and transactions. See [the user guide](USER_GUIDE.md) for relationships and backup scope. The application needs write access to its data directory.

## Desktop packaging

After validating desktop execution:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller FinBee.spec
```

The specification names the executable FinBee and bundles templates, static, and instance. The tracked instance/.gitkeep is only an empty-directory placeholder. Build from a clean checkout before running the app, or review instance/ so personal financial data is never bundled. No build success or downloadable executable is claimed by this guide.

## Troubleshooting

| Symptom | Explanation / check |
| --- | --- |
| TemplateNotFound | Confirm templates/ was included when downloading/copying the repository |
| Missing styling/icon | Confirm static/ resources and browser paths |
| No module named ... | Check isolated environment and dependency list |
| Database cannot be opened/written | BASE_DIR and directory permissions |
| Desktop window fails | Webview runtime and Waitress startup |
| Build cannot find data files | Check the templates/, static/, instance/ paths expected by FinBee.spec |

Historical build logs are not part of the current distributable source; consult actual build output locally.

## Test isolation

The restored tests/conftest.py imports the app before changing its database configuration and later drops tables. Run these legacy tests only in a disposable copy with no valuable database. Merely setting TESTING does not guarantee an isolated database. The local original data was not used during this update.

## Verification recorded for this restoration

An isolated temporary copy with synthetic records passed registration/login redirects and HTTP 200 checks for home, accounts, transactions, dashboard, insights, profile, import page, JSON export, CSV export, transaction-edit page, stylesheet, icon, and generic avatar. The environment used Python 3.10 and the web dependency versions in requirements.txt.

These are smoke checks, not proof of full correctness. The restored legacy pytest suite, actual JSON round-trip semantics, desktop GUI, and executable build were not validated. No personal database or uploaded photo was copied into the test.
