"""pytest 共通フィクスチャ。

各テストはテナント acme / globex の 2 つを持つ使い捨て SQLite で動く。
"""

from __future__ import annotations

import pytest

from app import seed
from app.common import db
from app.main import create_app


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "expenses.db"
    conn = db.connect(path)
    try:
        seed.seed(conn)
    finally:
        conn.close()
    return path


@pytest.fixture
def app(db_path):
    application = create_app(db_path)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def auth(token: str) -> dict[str, str]:
    """Authorization ヘッダを組み立てる。"""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice_headers():
    """テナント acme のユーザー。"""
    return auth(seed.TOKEN_ALICE)


@pytest.fixture
def bob_headers():
    """テナント globex のユーザー。"""
    return auth(seed.TOKEN_BOB)


@pytest.fixture
def carol_headers():
    """テナント acme のユーザー（alice の同僚）。"""
    return auth(seed.TOKEN_CAROL)
