# Campus IT Helpdesk ServiceHub

MSA University · CSE362c/CSE5531 · Fall 2026

Small local course application. J1 browse public IT articles, J2 submit persisted tickets, J3 administrator review and status updates. This is not an Internet-deployed service.

## Stack
Python 3.10+, Flask, SQLite, HTML/CSS/vanilla JavaScript, pytest and GitHub Actions.

## Windows setup (PowerShell)
1. python -m venv .venv
2. .venv\Scripts\Activate.ps1
3. python -m pip install -r requirements.txt
4. flask --app helpdesk init-db
5. flask --app helpdesk create-admin --username itadmin
6. flask --app helpdesk run --debug

Step 5 asks for a password (12-128 characters). Never put it in Git or the terminal command arguments. There is no default administrator and no web admin registration.

Open the student portal at http://127.0.0.1:5000/ and the staff interface at http://127.0.0.1:5000/admin.

For Linux/macOS, activate with: source .venv/bin/activate

Run tests: python -m pytest -q

## Journeys
- J1: GET /api/articles?q=...&category=... to browse IT support articles.
- J2: POST /api/tickets to validate and create an SQLite ticket, returning HTTP 201.
- J3: Log in from /admin, GET /api/tickets and GET /api/tickets/<id>, PATCH status and DELETE resolved tickets.

## Admin API
- GET /api/admin/session: authentication status and CSRF token.
- POST /api/admin/login: JSON username/password and X-CSRF-Token header.
- POST /api/admin/logout: session and X-CSRF-Token required.
- GET /api/tickets?status=: staff only (contains private contact emails).
- GET /api/tickets/<id>: staff only.
- PATCH /api/tickets/<id>: staff, CSRF, JSON {"status":"IN_PROGRESS"}.
- DELETE /api/tickets/<id>: staff, CSRF, resolved tickets only.

Workflow: OPEN -> IN_PROGRESS -> RESOLVED (or OPEN -> RESOLVED). Resolved tickets cannot reopen; backward transitions get HTTP 409. Missing credentials get 401; missing/invalid CSRF 403; invalid data 400; missing ticket 404.

## Security and persistence
Admin password hashes use Werkzeug. The Flask session signing key is generated once in instance/.session_secret with private permissions and survives restarts. The instance directory is excluded from Git. Alternatively provide HELPDESK_SECRET_KEY (32+ characters) via environment. Cookies are HttpOnly and SameSite=Lax. All staff ticket routes verify a live admin record server-side. Signed-in browser sends X-CSRF-Token on mutations. Parameterized SQL and DOM textContent avoid SQL/HTML injection. Security headers include CSP and no-cache for private APIs.

## Limitations
Local demonstration only. For deployment, add HTTPS and Secure cookies, login rate limiting, operator monitoring and admin audit logs. Genuine diagnosis evidence, mobile/accessibility/compatibility testing, final report, presentation and final release tag remain future milestone work. Never commit secrets or real student ticket data.
