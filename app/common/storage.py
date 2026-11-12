"""エクスポート成果物のファイルパス生成。

このモジュールの `resolve_export_path()` は、**ユーザー入力をファイルパスに一切混入させない**
ことを保証する。呼び出し側（`app/exporter.py`）はこの戻り値をシェルコマンドに渡すが、
パスはサーバ生成の UUID と許可リスト済み拡張子のみで構成されるため、シェルメタ文字は
構造上入り込めない。
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

EXPORT_ROOT = Path("/tmp/cm-workshop/exports")

# 出力を許可する拡張子。ここにない値は一切受け付けない。
ALLOWED_EXTENSIONS = frozenset({"csv", "pdf", "xlsx"})

# レポート ID は UUID 形式でなければならない。
_UUID_RE = re.compile(r"\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")


class UnsafeExportRequest(ValueError):
    """エクスポート要求が検証を通らなかった。"""


def resolve_export_path(report_id: str, extension: str) -> Path:
    """エクスポート先の絶対パスを生成して返す。

    引数 `report_id` は検証のみに使い、生成されるパスには含めない。
    ファイル名はサーバ側で新規に採番した UUID4 の hex 表現とする。

    Raises:
        UnsafeExportRequest: report_id が UUID 形式でない、または拡張子が許可外。
    """
    if not _UUID_RE.match(report_id):
        raise UnsafeExportRequest(f"report_id must be a UUID: {report_id!r}")

    normalized_ext = extension.lower().lstrip(".")
    if normalized_ext not in ALLOWED_EXTENSIONS:
        raise UnsafeExportRequest(f"extension not allowed: {extension!r}")

    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)

    # ファイル名はユーザー入力から完全に独立している。
    server_generated_name = uuid.uuid4().hex
    return EXPORT_ROOT / f"{server_generated_name}.{normalized_ext}"
