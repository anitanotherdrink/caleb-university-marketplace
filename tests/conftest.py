"""Pytest fixtures: each test runs against a fresh, isolated SQLite DB.

Config values are read live (``config.X`` at call time), so pointing
``config.DB_URL`` at a temp file and resetting the engine singleton is enough —
no module reloading required.
"""
from __future__ import annotations

import pytest

import config
from services import auth, db


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    config.DB_URL = f"sqlite:///{tmp_path / 'test.db'}"
    config.INSTITUTION_DOMAIN = "calebuniversity.edu.ng"
    db._engine = None
    db._SessionFactory = None
    auth._failed.clear()
    db.init_db(seed=True)
    yield
    db._engine = None
    db._SessionFactory = None
