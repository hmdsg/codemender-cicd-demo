"""教材用のシードデータ投入。

2 つのテナント（acme / globex）を作り、それぞれにユーザー・レポート・添付を
用意する。テナント分離の確認に使う。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.common import db

# 固定 UUID にしておくと、ID をコピペしやすい。
TENANT_ACME = "11111111-1111-4111-8111-111111111111"
TENANT_GLOBEX = "22222222-2222-4222-8222-222222222222"

USER_ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"  # acme
USER_BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"  # globex
USER_CAROL = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"  # acme, alice の同僚

TOKEN_ALICE = "acme-alice-token"
TOKEN_BOB = "globex-bob-token"
TOKEN_CAROL = "acme-carol-token"

REPORT_ACME = "33333333-3333-4333-8333-333333333333"
REPORT_ACME_MEETING = "33333333-3333-4333-8333-333333333334"
REPORT_ACME_SUPPLIES = "33333333-3333-4333-8333-333333333335"
REPORT_GLOBEX = "44444444-4444-4444-8444-444444444444"

ATTACHMENT_ACME = "55555555-5555-4555-8555-555555555555"
ATTACHMENT_GLOBEX = "66666666-6666-4666-8666-666666666666"

COMMENT_ALICE = "77777777-7777-4777-8777-777777777777"


def seed(conn: sqlite3.Connection) -> None:
    """冪等にシードデータを投入する。"""
    db.init_schema(conn)

    conn.executemany(
        "INSERT OR REPLACE INTO tenants (id, name) VALUES (?, ?)",
        [(TENANT_ACME, "Acme Inc."), (TENANT_GLOBEX, "Globex Corp.")],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO users (id, tenant_id, email, api_token) VALUES (?, ?, ?, ?)",
        [
            (USER_ALICE, TENANT_ACME, "alice@acme.example", TOKEN_ALICE),
            (USER_BOB, TENANT_GLOBEX, "bob@globex.example", TOKEN_BOB),
            (USER_CAROL, TENANT_ACME, "carol@acme.example", TOKEN_CAROL),
        ],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO reports (id, tenant_id, author_id, title, amount_jpy, status)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            (REPORT_ACME, TENANT_ACME, USER_ALICE, "出張費 2026-07 大阪", 48200, "submitted"),
            (REPORT_ACME_MEETING, TENANT_ACME, USER_ALICE, "会議費 2026-06 東京", 12800, "approved"),
            (REPORT_ACME_SUPPLIES, TENANT_ACME, USER_ALICE, "備品購入 2026-05", 33000, "approved"),
            (REPORT_GLOBEX, TENANT_GLOBEX, USER_BOB, "買収案件 デューデリ費用", 1250000, "draft"),
        ],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO attachments (id, tenant_id, report_id, filename, content)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (ATTACHMENT_ACME, TENANT_ACME, REPORT_ACME, "receipt-osaka.txt", "新幹線 東京-新大阪 28,600円"),
            (
                ATTACHMENT_GLOBEX,
                TENANT_GLOBEX,
                REPORT_GLOBEX,
                "dd-invoice.txt",
                "【社外秘】買収対象: Initech 社 / 想定価格 82億円",
            ),
        ],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO comments (id, tenant_id, report_id, author_id, body)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (COMMENT_ALICE, TENANT_ACME, REPORT_ACME, USER_ALICE, "領収書は添付済みです。承認お願いします。"),
        ],
    )
    conn.commit()


def main() -> None:
    path = Path(db.DEFAULT_DB_PATH)
    conn = db.connect(path)
    try:
        seed(conn)
    finally:
        conn.close()
    print(f"[seed] seeded {path}")


if __name__ == "__main__":
    main()
