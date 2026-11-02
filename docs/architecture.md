# Scope and architecture

Browser (HTML/CSS/JS) -> Flask JSON endpoints -> SQLite persistent storage.

- J1: Search/filter event -> GET /api/articles -> SQLite SELECT -> JSON -> rendered articles.
- J2: Ticket form -> POST /api/tickets -> server validation -> SQLite INSERT -> HTTP 201 -> confirmation.
- J3 (future): Authenticated administrator -> GET/PATCH/DELETE tickets -> session/CSRF/authorization and status rules -> persisted change -> refreshed UI.

Database tables: knowledge_articles (id, title, category, body) and tickets (id, title, description, category, contact_email, status, created_at, updated_at). Legal status values: OPEN, IN_PROGRESS, RESOLVED.

Planned business rule: Resolved tickets cannot be reopened by a direct status transition. No admin endpoints or user accounts exist in this starter.

Evidence requirements: Real requests/responses, data persistence after restart, positive/negative/business-rule and security tests, responsive accessibility, browser compatibility, a genuine insufficient-evidence diagnosis, regression verification, and a final tagged release. No screenshots or evidence are fabricated.
