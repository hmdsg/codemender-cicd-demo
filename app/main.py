"""Flask アプリケーションファクトリ。

    uv run flask --app app.main:create_app run

教材アプリのため、実運用向けの設定（HTTPS 強制、レートリミット、
シークレット管理など）は意図的に省略している。
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify

from app import attachments, comments, exporter, reports, webhook
from app.common import db


def create_app(db_path: Path | str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path) if db_path else str(db.DEFAULT_DB_PATH)

    app.register_blueprint(reports.bp)
    app.register_blueprint(attachments.bp)
    app.register_blueprint(exporter.bp)
    app.register_blueprint(webhook.bp)
    app.register_blueprint(comments.bp)

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app
