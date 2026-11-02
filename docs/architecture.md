# Architecture and J1/J2/J3 contracts

Browser -> Flask API -> SQLite (real persistent records). Client state and browser events are managed by vanilla JavaScript; Flask validates before changing data.

J1: Search/filter -> GET /api/articles -> SELECT knowledge_articles -> JSON -> cards.
J2: Validated form -> POST /api/tickets -> INSERT tickets -> HTTP 201 -> ticket confirmation.
J3: Create administrator using local CLI -> login via signed session -> GET /api/tickets -> review -> PATCH state -> persisted UPDATE -> refreshed admin UI.

SQLite tables:
- knowledge_articles: id, title, category, body.
- tickets: id, title, description, category, contact_email, status, created_at, updated_at.
- admins: id, username, password_hash.

Business rules: OPEN can progress to IN_PROGRESS or RESOLVED, IN_PROGRESS can progress only to RESOLVED, and RESOLVED is terminal. Only RESOLVED tickets can be deleted.

Security: administrator accounts are explicitly provisioned locally; no default password or public registration. Password hashes are not plaintext. Signed HttpOnly SameSite=Lax session with generated private persistent key; fresh CSRF token after login. Admin-only routes check ID against stored admins, all mutations check CSRF. Cookies are not Secure because this is a local HTTP-only development server. Restrict to localhost; enable HTTPS and Secure cookies for production.

Testing: tests cover J1/J2 existing journeys, positive and negative J3, unauthorized access, validation, persisted update, status invariants, CSRF failures, logout, and secret handling. Browser screenshots, true restart evidence, defect diagnosis and regression record must be collected during subsequent milestones. Do not fabricate evidence.
