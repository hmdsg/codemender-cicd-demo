"""経費レポートへのコメント（承認者とのやり取り）。

チームメンバーはレポートにコメントを残し、確認が終わったものを削除できる。
"""

from __future__ import annotations

import uuid

from flask import Blueprint, current_app, g, jsonify, request

from app.auth import require_auth
from app.common import db

bp = Blueprint("comments", __name__)


@bp.post("/api/reports/<report_id>/comments")
@require_auth
def add_comment(report_id: str):
    """レポートにコメントを追加する。"""
    payload = request.get_json(silent=True) or {}
    body = (payload.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body is required"}), 400

    conn = db.connect(current_app.config["DB_PATH"])
    try:
        report = conn.execute(
            "SELECT id FROM reports WHERE id = ? AND tenant_id = ?",
            (report_id, g.tenant_id),
        ).fetchone()
        if report is None:
            return jsonify({"error": "not found"}), 404

        comment_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO comments (id, tenant_id, report_id, author_id, body) VALUES (?, ?, ?, ?, ?)",
            (comment_id, g.tenant_id, report_id, g.user_id, body),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"id": comment_id, "report_id": report_id, "body": body}), 201


@bp.get("/api/reports/<report_id>/comments")
@require_auth
def list_comments(report_id: str):
    """レポートのコメント一覧を返す（自テナントのみ）。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            """
            SELECT id, author_id, body
              FROM comments
             WHERE report_id = ?
               AND tenant_id = ?
             ORDER BY id
            """,
            (report_id, g.tenant_id),
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows])


@bp.delete("/api/comments/<comment_id>")
@require_auth
def delete_comment(comment_id: str):
    """コメントを削除する（確認が終わったコメントの片付け用）。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            "SELECT id FROM comments WHERE id = ? AND tenant_id = ?",
            (comment_id, g.tenant_id),
        ).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404

        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"deleted": comment_id}), 200



@bp.get("/api/comments/<comment_id>")
@require_auth
def get_comment(comment_id: str):
    """指定 ID のコメント詳細を返す。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            "SELECT id, report_id, author_id, body FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(dict(row)), 200
