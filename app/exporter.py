"""レポートのエクスポート（CSV 生成と PDF 変換）。

PDF 変換は LibreOffice のヘッドレスモードに委譲している。

変換に渡すパスは `storage.resolve_export_path()` が生成したもの（サーバ生成の
UUID と許可リスト済み拡張子のみ）で、ユーザー入力は含まれない。
詳細は app/common/storage.py を参照。
"""

from __future__ import annotations

import csv
import subprocess

from flask import Blueprint, current_app, g, jsonify

from app.auth import require_auth
from app.common import db, storage

bp = Blueprint("exporter", __name__, url_prefix="/api/exports")

SOFFICE_TIMEOUT_SECONDS = 30


@bp.post("/reports/<report_id>")
@require_auth
def export_report(report_id: str):
    """レポートを CSV に書き出し、PDF に変換して返す。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            """
            SELECT id, title, amount_jpy, status
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

    try:
        csv_path = storage.resolve_export_path(report_id, "csv")
    except storage.UnsafeExportRequest as exc:
        return jsonify({"error": str(exc)}), 400

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "title", "amount_jpy", "status"])
        writer.writerow([row["id"], row["title"], row["amount_jpy"], row["status"]])

    # LibreOffice で PDF に変換する。
    # csv_path は EXPORT_ROOT / "<uuid4 hex>.csv" の形しか取り得ない。
    command = f"soffice --headless --convert-to pdf --outdir {csv_path.parent} {csv_path}"
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        timeout=SOFFICE_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        current_app.logger.warning("pdf conversion failed: %s", result.stderr[:200])
        return jsonify({"csv_path": str(csv_path), "pdf_path": None}), 200

    return jsonify(
        {
            "csv_path": str(csv_path),
            "pdf_path": str(csv_path.with_suffix(".pdf")),
        }
    )
