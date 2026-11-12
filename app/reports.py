"""経費レポートのエンドポイント。

テナント分離の観点では、このモジュールの `get_report()` / `list_reports()` が
**正しい実装のお手本**である。いずれも WHERE 句に `tenant_id = ?` を含めている。
"""

from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from app.auth import require_auth
from app.common import db

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/<report_id>")
@require_auth
def get_report(report_id: str):
    """単一のレポートを取得する。

    テナント分離: WHERE 句で tenant_id を必ず絞り込む。
    プレースホルダを使うので SQL インジェクションもない。
    """
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            """
            SELECT id, tenant_id, author_id, title, amount_jpy, status
              FROM reports
             WHERE id = ?
               AND tenant_id = ?
            """,
            (report_id, g.tenant_id),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(
        {
            "id": row["id"],
            "title": row["title"],
            "amount_jpy": row["amount_jpy"],
            "status": row["status"],
        }
    )


@bp.get("")
@require_auth
def list_reports():
    """自テナントのレポート一覧を返す。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            """
            SELECT id, title, amount_jpy, status
              FROM reports
             WHERE tenant_id = ?
             ORDER BY title
            """,
            (g.tenant_id,),
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows])


@bp.get("/search/by-title")
@require_auth
def search_reports():
    """タイトル部分一致でレポートを検索する。

    ソート順はクライアントが `order` パラメータで指定できる。
    """
    term = request.args.get("q", "")
    order = request.args.get("order", "ASC")

    conn = db.connect(current_app.config["DB_PATH"])
    try:
        query = (
            "SELECT id, title, amount_jpy FROM reports "
            f"WHERE tenant_id = '{g.tenant_id}' AND title LIKE '%{term}%' "
            f"ORDER BY title {order}"
        )
        rows = conn.execute(query).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows])
