"""認証とテナントコンテキストの確立。

このアプリはマルチテナント SaaS である。**あらゆるデータアクセスは
`g.tenant_id` でスコープされなければならない。** これが本アプリの
最重要のセキュリティ不変条件である。

`require_auth` デコレータは Authorization ヘッダの API トークンを検証し、
リクエストコンテキストに以下を設定する:

  g.user_id    : 認証されたユーザーの ID
  g.tenant_id  : そのユーザーが所属するテナントの ID

各エンドポイントは、この `g.tenant_id` を SQL の WHERE 句に含める責務を負う。
"""

from __future__ import annotations

import functools
from typing import Callable

from flask import current_app, g, jsonify, request

from app.common import db


class AuthenticationError(Exception):
    """認証に失敗した。"""


def _extract_token() -> str | None:
    """Authorization: Bearer <token> からトークンを取り出す。"""
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix):
        return None
    token = header[len(prefix):].strip()
    return token or None


def resolve_principal(api_token: str) -> tuple[str, str] | None:
    """API トークンから (user_id, tenant_id) を解決する。

    見つからなければ None を返す。
    """
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            "SELECT id, tenant_id FROM users WHERE api_token = ?",
            (api_token,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return row["id"], row["tenant_id"]


def require_auth(view: Callable) -> Callable:
    """認証を必須にし、g.user_id / g.tenant_id を設定するデコレータ。"""

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if token is None:
            return jsonify({"error": "missing bearer token"}), 401

        principal = resolve_principal(token)
        if principal is None:
            return jsonify({"error": "invalid token"}), 401

        g.user_id, g.tenant_id = principal
        return view(*args, **kwargs)

    return wrapper
