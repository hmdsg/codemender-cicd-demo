"""添付ファイルエンドポイントのテスト。

正常系（自テナントの添付は読める・他人の添付は読めない・未認証は 401）を
回帰ガードする。
"""

from __future__ import annotations

from app import seed


def test_owner_can_download_own_attachment(client, alice_headers):
    """★ 回帰ガード ★

    自テナントの添付は必ずダウンロードできること。
    テナント越境の欠陥を「全部 403 にする」ような雑な修正を防ぐ。
    """
    res = client.get(f"/api/attachments/{seed.ATTACHMENT_ACME}", headers=alice_headers)
    assert res.status_code == 200

    body = res.get_json()
    assert body["filename"] == "receipt-osaka.txt"
    assert "新幹線" in body["content"]


def test_other_tenant_owner_can_download_their_own_attachment(client, bob_headers):
    """★ 回帰ガード ★ globex 側でも同様に自テナントの添付は読めること。"""
    res = client.get(f"/api/attachments/{seed.ATTACHMENT_GLOBEX}", headers=bob_headers)
    assert res.status_code == 200
    assert res.get_json()["filename"] == "dd-invoice.txt"


def test_unknown_attachment_is_not_found(client, alice_headers):
    res = client.get(
        "/api/attachments/99999999-9999-4999-8999-999999999999", headers=alice_headers
    )
    assert res.status_code == 404


def test_download_requires_authentication(client):
    assert client.get(f"/api/attachments/{seed.ATTACHMENT_ACME}").status_code == 401


def test_list_attachments_is_tenant_scoped(client, alice_headers):
    """一覧 API は JOIN で tenant を絞っているので越境しない。"""
    own = client.get(
        f"/api/attachments?report_id={seed.REPORT_ACME}", headers=alice_headers
    ).get_json()
    assert [a["id"] for a in own] == [seed.ATTACHMENT_ACME]

    other = client.get(
        f"/api/attachments?report_id={seed.REPORT_GLOBEX}", headers=alice_headers
    ).get_json()
    assert other == []
