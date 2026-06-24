"""Database engine + session factory and one-time init/seed (PRD §7.4, §9.4).

The same SQLAlchemy models run on SQLite (dev) and Postgres (prod); only DB_URL
changes. ``init_db`` is idempotent and seeds a starter category set plus a
default admin so the platform is operable on first run.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import config
from models.db_models import Base, Category, User

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None

DEFAULT_CATEGORIES = [
    ("Textbooks", "Course books, study guides and past questions"),
    ("Electronics & Gadgets", "Phones, laptops, accessories and chargers"),
    ("Clothing & Fashion", "Clothes, shoes, bags and accessories"),
    ("Furniture & Hostel", "Beds, fans, kettles and hostel essentials"),
    ("Services", "Tutoring, tailoring, hairdressing and more"),
    ("Other", "Anything else"),
]


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    global _engine, _SessionFactory
    if _engine is None:
        _ensure_sqlite_dir(config.DB_URL)
        connect_args = {}
        if config.DB_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            config.DB_URL, connect_args=connect_args, future=True
        )
        if config.DB_URL.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _fk_pragma(dbapi_con, _):  # pragma: no cover - trivial
                dbapi_con.execute("PRAGMA foreign_keys=ON")

        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _SessionFactory is None:
        get_engine()
    assert _SessionFactory is not None
    return _SessionFactory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope: commit on success, rollback on error."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(seed: bool = True) -> None:
    """Create tables (idempotent) and seed starter data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    if not seed:
        return
    from services import security  # local import to avoid cycle

    with session_scope() as s:
        if s.query(Category).count() == 0:
            for name, desc in DEFAULT_CATEGORIES:
                s.add(Category(name=name, description=desc))

        if s.query(User).filter(User.role == "admin").count() == 0:
            admin_email = os.environ.get(
                "ADMIN_EMAIL", f"admin@{config.INSTITUTION_DOMAIN}"
            )
            admin_pw = os.environ.get("ADMIN_PASSWORD", "Admin#12345")
            s.add(
                User(
                    full_name="Platform Admin",
                    email=admin_email.lower(),
                    password_hash=security.hash_password(admin_pw),
                    role="admin",
                    is_verified=True,
                    is_active=True,
                )
            )
