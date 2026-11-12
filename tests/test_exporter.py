"""エクスポートエンドポイントのテスト。

LibreOffice (soffice) がインストールされていなくても通るようにしている。
変換に失敗した場合は pdf_path が None になるだけで、CSV 生成は成功する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import seed
from app.common import storage


def test_export_own_report_writes_csv(client, alice_headers):
    """★ 回帰ガード ★ 自テナントのレポートは CSV に書き出せること。"""
    res = client.post(f"/api/exports/reports/{seed.REPORT_ACME}", headers=alice_headers)
    assert res.status_code == 200

    csv_path = Path(res.get_json()["csv_path"])
    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8")
    assert "出張費 2026-07 大阪" in content, "★ 回帰ガード ★ 日本語タイトルが壊れないこと"


def test_export_of_other_tenant_report_is_not_found(client, alice_headers):
    res = client.post(f"/api/exports/reports/{seed.REPORT_GLOBEX}", headers=alice_headers)
    assert res.status_code == 404


def test_export_requires_authentication(client):
    assert client.post(f"/api/exports/reports/{seed.REPORT_ACME}").status_code == 401


@pytest.mark.parametrize(
    "bad_id",
    [
        "not-a-uuid",
        "../../etc/passwd",
        "$(id)",
        "'; touch /tmp/pwned; #",
    ],
)
def test_resolve_export_path_rejects_non_uuid(bad_id):
    """report_id が UUID でなければパス生成の時点で拒否される。"""
    with pytest.raises(storage.UnsafeExportRequest):
        storage.resolve_export_path(bad_id, "csv")


def test_resolve_export_path_rejects_unknown_extension():
    with pytest.raises(storage.UnsafeExportRequest):
        storage.resolve_export_path(seed.REPORT_ACME, "sh")


def test_resolve_export_path_never_contains_user_input():
    """生成されたパスは UUID hex と許可拡張子のみで構成される。

    エクスポート経路にユーザー入力が混入しないことの回帰ガード。
    """
    path = storage.resolve_export_path(seed.REPORT_ACME, "csv")

    assert path.parent == storage.EXPORT_ROOT
    assert path.suffix == ".csv"
    assert path.stem.isalnum() and len(path.stem) == 32
    assert seed.REPORT_ACME not in str(path)
