# Campus IT Helpdesk ServiceHub

MSA University · CSE362c / CSE5531 · Fall 2026

Starter application for the team project. This is **not the complete course submission**.

## User journeys

- **J1 (starter):** Search and filter public support articles stored in SQLite.
- **J2 (starter):** Submit an IT ticket; Flask validates it and persists it in SQLite.
- **J3 (planned, not implemented):** An authenticated IT administrator reviews tickets, updates ticket status, and performs authorized CRUD actions.

## Stack
Python 3.10+, Flask, SQLite, HTML/CSS, vanilla JavaScript and pytest.

## Run locally
Run these commands from the repository root:

1. Create a virtual environment: python -m venv .venv
2. Activate it: .venv\Scripts\Activate.ps1 (PowerShell), or source .venv/bin/activate (Linux/macOS)
3. Install requirements: python -m pip install -r requirements.txt
4. Initialize the database: flask --app helpdesk init-db
5. Start development server: flask --app helpdesk run --debug
6. Open http://127.0.0.1:5000

The local SQLite database lives under instance/ and is excluded from Git. Running init-db again preserves existing tickets.

Run tests: python -m pytest -q

## Starter API

| Method | Endpoint | Status |
| --- | --- | --- |
| GET | /api/health | Implemented |
| GET | /api/articles?q=&category= | Implemented |
| POST | /api/tickets | Implemented |
| POST | /api/admin/login | Planned |
| GET | /api/tickets | Planned |
| PATCH | /api/tickets/<id> | Planned |
| DELETE | /api/tickets/<id> | Planned |

Submit tickets as JSON with title (5–120 chars), description (10–2000 chars), category (wifi, hardware, software, account), and contact_email.

## Repository map

- helpdesk/: Flask factory, SQLite, schema, frontend.
- tests/: Starter API and database tests.
- docs/: Architecture and project constraints.
- evidence/: Intended folders for real verification evidence.
- .github/workflows/tests.yml: Runs tests for commits and PRs.

## Required work before final submission

Implement authentication with hashed passwords and session/CSRF protection; finish authorized J3 and CRUD; verify persistent storage across restarts; demonstrate security and business-rule tests; collect genuine diagnosis and regression evidence; complete report and presentation.

Development mode is local-only. Do not commit real passwords, private tickets or any production credentials.
