# Caleb University Student Marketplace

A secure, web-based **consumer-to-consumer (C2C) e-commerce platform** for
verified Caleb University students. Students list, browse, search and order
campus items (textbooks, gadgets, clothing, hostel goods, services) without
exposing personal contacts to strangers. Payment is settled **in person on
campus** — checkout is simulated and moves no money.

Built per `PRD_Caleb_Marketplace.md`, which traces to the thesis *Design and
Implementation of a Secure Web-Based E-Commerce Platform for Caleb University
Students* (Chapters 1–3).

**Stack:** Python · Streamlit (presentation) · service layer (application) ·
SQLAlchemy + SQLite/Postgres (data) — the thesis three-tier model.

---

## Quick start

```bash
# 1. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. (Optional) configure environment — sane dev defaults apply without this
cp .env.example .env        # edit if you want SMTP / a custom domain

# 3. Seed demo students + listings (optional but recommended)
python seed_demo.py

# 4. Run the app
streamlit run app.py
# open http://localhost:8501
```

### Demo accounts (after `seed_demo.py`)

All seeded students are pre-verified and share the password **`Demo#Pass123`**, so
you can log in as several different users to try buyer/seller interactions.

| Role    | Email                                  |
|---------|----------------------------------------|
| Admin   | `admin@calebuniversity.edu.ng` (pw `Admin#12345`) |
| Student | `ada.obi@calebuniversity.edu.ng`       |
| Student | `tunde.bello@calebuniversity.edu.ng`   |
| Student | `chioma.eze@calebuniversity.edu.ng`    |
| Student | `daniel.okoro@calebuniversity.edu.ng`  |
| Student | `fatima.sani@calebuniversity.edu.ng`   |
| Student | `emeka.nwosu@calebuniversity.edu.ng`   |

> **Registering a new account:** use any `@calebuniversity.edu.ng` email. If an
> SMTP server is configured, a verification link is emailed; otherwise the link
> is printed to the console **and** a one-click "Verify my email now (dev mode)"
> button appears on the register screen so you can finish locally. This dev
> shortcut is automatically disabled once SMTP is configured (i.e. in
> production).

---

## What's implemented (PRD coverage)

| PRD feature | Where |
|---|---|
| FR-001 Registration (institutional-domain + password policy) | `services/auth.py`, `models/schemas.py`, `pages/register.py` |
| FR-002 Email verification (single-use, 24h token) | `services/auth.py`, `services/email.py`, `pages/verify.py` |
| FR-003/004 Login, logout, signed sessions, idle/absolute timeout, rate-limit | `services/auth.py`, `services/security.py`, `components/auth_gate.py` |
| FR-005 Profile management | `services/users.py`, `pages/profile.py` |
| FR-006/007/008 Listing create / edit / soft-delete | `services/catalog.py`, `pages/listing_editor.py`, `pages/my_listings.py` |
| FR-009 Image upload (size cap + content sniffing) | `services/catalog.py` |
| FR-010 Browse / search / filter (keyword, category, price) | `services/catalog.py`, `pages/browse.py` |
| FR-011 Cart + simulated checkout (price snapshot) | `services/orders.py`, `pages/cart.py` |
| FR-012 Order status lifecycle (legal transitions enforced) | `services/orders.py`, `pages/my_orders.py` |
| FR-013 RBAC + ownership checks | `components/auth_gate.py`, service-layer guards |
| FR-014 Administration (users, categories, oversight) | `services/admin.py`, `pages/admin_*.py` |

Security highlights: Argon2id password hashing (never plaintext, never logged),
HMAC-signed sessions, parameterized queries (no string-built SQL), upload
content-sniffing, generic auth errors (no user enumeration), least-privilege
ownership checks. See PRD §11.

---

## Project structure

```
app.py                 # router + auth gate + theming (st.navigation)
config.py              # env-driven configuration (secrets via env / st.secrets)
pages/                 # Streamlit screens (login, browse, cart, admin, …)
components/            # reusable UI (ui.py) + access control (auth_gate.py)
services/              # application tier: auth, catalog, orders, admin, users,
                       #   email, security, telemetry, db, errors
models/                # db_models.py (SQLAlchemy) + schemas.py (Pydantic)
tests/                 # pytest unit tests for the service layer
seed_demo.py           # demo data loader
data/                  # SQLite DB (dev)
media/                 # uploaded product images (non-executable)
.streamlit/config.toml # upload cap, XSRF protection, theme
```

---

## Testing

```bash
source .venv/bin/activate
pytest -q                       # 24 service-layer unit tests
pytest --cov=services --cov=models   # with coverage
```

Tests cover the institutional-domain check, password policy, the full
register→verify→login flow, login rate-limiting, image validation, filter
combination, ownership enforcement, price snapshotting, and the order
transition matrix.

---

## Configuration

All configuration is read from the environment (see `.env.example`). Nothing is
required for local dev. Key variables:

| Variable | Purpose | Dev default |
|---|---|---|
| `DB_URL` | Database connection | local SQLite |
| `INSTITUTION_DOMAIN` | Allowed registration domain | `calebuniversity.edu.ng` |
| `SESSION_SIGNING_KEY` | HMAC key for session tokens | dev placeholder |
| `SMTP_*` | Verification email delivery | console fallback if unset |
| `MEDIA_ROOT` | Product image storage path | `./media` |

For production, set a strong `SESSION_SIGNING_KEY`, point `DB_URL` at Postgres,
configure SMTP, and terminate TLS at a reverse proxy (PRD §13.2).

---

## Notes & deviations

- **Python version:** the PRD targets Python 3.11+. The code runs on 3.9+ as
  well — runtime type annotations use `typing.Optional`/`List` rather than
  PEP 604 `X | None` so it executes on older interpreters; behaviour is
  identical on 3.11+.
- **Admin account** is auto-created on first run (no self-service admin signup,
  per PRD §3.1). Override via `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars.
- Out of scope by design (PRD §2.2): live payments, native mobile apps,
  delivery/escrow, ratings, in-app chat.
