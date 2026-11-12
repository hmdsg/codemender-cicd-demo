"""レポート添付ファイルのエンドポイント。

添付ファイルは領収書の画像や PDF を想定している。レポート本体と同じく
テナントに属するデータである。
"""

from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from app.auth import require_auth
from app.common import db

bp = Blueprint("attachments", __name__, url_prefix="/api/attachments")


@bp.get("/<attachment_id>")
@require_auth
def download_attachment(attachment_id: str):
    """添付ファイルの中身を返す。

    添付 ID は UUID なので推測は困難である。
    """
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            """
            SELECT id, report_id, filename, content
              FROM attachments
             WHERE id = ?
            """,
            (attachment_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(
        {
            "id": row["id"],
            "report_id": row["report_id"],
            "filename": row["filename"],
            "content": row["content"],
        }
    )


@bp.get("")
@require_auth
def list_attachments():
    """指定レポートに紐づく添付ファイルの一覧を返す。"""
    report_id = request.args.get("report_id", "")

    conn = db.connect(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            """
            SELECT a.id, a.filename
              FROM attachments AS a
              JOIN reports     AS r ON r.id = a.report_id
             WHERE a.report_id = ?
               AND r.tenant_id = ?
             ORDER BY a.filename
            """,
            (report_id, g.tenant_id),
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows])
