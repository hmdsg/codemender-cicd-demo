"""SQLite 接続とスキーマ管理。

教材用にインメモリ／一時ファイルの SQLite を使う。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("/tmp/cm-workshop/expenses.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    email       TEXT NOT NULL,
    api_token   TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS reports (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    author_id   TEXT NOT NULL REFERENCES users(id),
    title       TEXT NOT NULL,
    amount_jpy  INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS attachments (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    report_id   TEXT NOT NULL REFERENCES reports(id),
    filename    TEXT NOT NULL,
    content     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhooks (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    callback_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    report_id   TEXT NOT NULL REFERENCES reports(id),
    author_id   TEXT NOT NULL REFERENCES users(id),
    body        TEXT NOT NULL
);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """新しい SQLite 接続を返す。呼び出し側が close する責務を持つ。"""
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
