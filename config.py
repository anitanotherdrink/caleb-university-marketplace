"""Central configuration. Reads from environment / .env with safe dev defaults.

Secrets and environment-specific values live here only (PRD §9.7). No secret
literals are committed; defaults are dev-only conveniences.
"""
from __future__ import annotations

import os
from pathlib import Path

try:  # optional: load a local .env if present
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

BASE_DIR = Path(__file__).resolve().parent


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# --- Data tier -------------------------------------------------------------
DB_URL: str = _get("DB_URL", f"sqlite:///{BASE_DIR / 'data' / 'marketplace.db'}")

# --- Identity / institution ------------------------------------------------
INSTITUTION_DOMAIN: str = _get("INSTITUTION_DOMAIN", "calebuniversity.edu.ng").lower()

# --- Sessions (PRD FR-004) -------------------------------------------------
SESSION_SIGNING_KEY: str = _get(
    "SESSION_SIGNING_KEY", "dev-only-insecure-key-change-in-production"
)
SESSION_IDLE_TIMEOUT_MIN: int = int(_get("SESSION_IDLE_TIMEOUT_MIN", "30"))
SESSION_ABSOLUTE_TIMEOUT_H: int = int(_get("SESSION_ABSOLUTE_TIMEOUT_H", "12"))

# --- Auth policy (PRD G-6) -------------------------------------------------
PASSWORD_MIN_LENGTH: int = 10
LOGIN_MAX_ATTEMPTS: int = 5
LOGIN_LOCKOUT_MIN: int = 5

# --- Email verification (PRD FR-002) --------------------------------------
TOKEN_TTL_HOURS: int = 24
APP_BASE_URL: str = _get("APP_BASE_URL", "http://localhost:8501")

# --- Media (PRD FR-009) ----------------------------------------------------
MEDIA_ROOT: Path = Path(_get("MEDIA_ROOT", str(BASE_DIR / "media")))
MAX_IMAGE_BYTES: int = 5 * 1024 * 1024
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}

# --- SMTP (optional in dev) ------------------------------------------------
SMTP_HOST: str = _get("SMTP_HOST")
SMTP_PORT: int = int(_get("SMTP_PORT", "587") or "587")
SMTP_USER: str = _get("SMTP_USER")
SMTP_PASSWORD: str = _get("SMTP_PASSWORD")
SMTP_FROM: str = _get("SMTP_FROM", f"no-reply@{INSTITUTION_DOMAIN}")

# --- Formatting (PRD §9.11) ------------------------------------------------
CURRENCY_SYMBOL = "₦"  # Naira
TIMEZONE = "Africa/Lagos"


def smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
