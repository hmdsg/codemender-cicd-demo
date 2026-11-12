"""Webhook 登録と通知の送信。

テナントはレポート承認時に通知を受け取るコールバック URL を登録できる。
"""

from __future__ import annotations

import uuid

import requests
from flask import Blueprint, current_app, g, jsonify, request

from app.auth import require_auth
from app.common import db

bp = Blueprint("webhook", __name__, url_prefix="/api/webhooks")

CALLBACK_TIMEOUT_SECONDS = 5


@bp.post("")
@require_auth
def register_webhook():
    """コールバック URL を登録し、疎通確認のためのプローブを送信する。"""
    payload = request.get_json(silent=True) or {}
    callback_url = payload.get("callback_url", "")

    if not callback_url:
        return jsonify({"error": "callback_url is required"}), 400

    # 登録前に疎通確認する。
    probe_body = None
    try:
        probe = requests.get(callback_url, timeout=CALLBACK_TIMEOUT_SECONDS)
        probe_body = probe.text[:500]
        reachable = probe.ok
    except requests.RequestException as exc:
        current_app.logger.info("callback probe failed: %s", exc)
        reachable = False

    webhook_id = str(uuid.uuid4())
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        conn.execute(
            "INSERT INTO webhooks (id, tenant_id, callback_url) VALUES (?, ?, ?)",
            (webhook_id, g.tenant_id, callback_url),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify(
        {
            "id": webhook_id,
            "callback_url": callback_url,
            "reachable": reachable,
            "probe_response": probe_body,
        }
    ), 201


@bp.get("")
@require_auth
def list_webhooks():
    """自テナントの Webhook 一覧を返す。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            "SELECT id, callback_url FROM webhooks WHERE tenant_id = ? ORDER BY id",
            (g.tenant_id,),
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows])
