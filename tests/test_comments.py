"""レポートコメントのテスト。

正常系（自分のコメントは追加・削除できる・他テナントからは触れない）を
回帰ガードする。
"""

from __future__ import annotations

from app import seed


def test_can_add_and_list_comment(client, alice_headers):
    res = client.post(
        f"/api/reports/{seed.REPORT_ACME}/comments",
        headers=alice_headers,
        json={"body": "確認しました"},
    )
    assert res.status_code == 201

    listed = client.get(
        f"/api/reports/{seed.REPORT_ACME}/comments", headers=alice_headers
    ).get_json()
    bodies = [c["body"] for c in listed]
    assert "確認しました" in bodies


def test_cannot_comment_on_other_tenants_report(client, bob_headers):
    res = client.post(
        f"/api/reports/{seed.REPORT_ACME}/comments",
        headers=bob_headers,
        json={"body": "覗いてみる"},
    )
    assert res.status_code == 404


def test_comment_list_is_tenant_scoped(client, bob_headers):
    """globex から acme のレポートのコメントは見えないこと。"""
    res = client.get(f"/api/reports/{seed.REPORT_ACME}/comments", headers=bob_headers)
    assert res.status_code == 200
    assert res.get_json() == []


def test_owner_can_delete_own_comment(client, alice_headers):
    """★ 回帰ガード ★ 自分のコメントは削除できること。"""
    res = client.delete(f"/api/comments/{seed.COMMENT_ALICE}", headers=alice_headers)
    assert res.status_code == 200

    listed = client.get(
        f"/api/reports/{seed.REPORT_ACME}/comments", headers=alice_headers
    ).get_json()
    assert seed.COMMENT_ALICE not in [c["id"] for c in listed]


def test_other_tenant_cannot_delete_comment(client, alice_headers, bob_headers):
    """★ 回帰ガード ★ テナント越境の削除は 404 になること。"""
    res = client.delete(f"/api/comments/{seed.COMMENT_ALICE}", headers=bob_headers)
    assert res.status_code == 404

    # 消えていないことも確認する。
    listed = client.get(
        f"/api/reports/{seed.REPORT_ACME}/comments", headers=alice_headers
    ).get_json()
    assert seed.COMMENT_ALICE in [c["id"] for c in listed]


def test_delete_requires_authentication(client):
    assert client.delete(f"/api/comments/{seed.COMMENT_ALICE}").status_code == 401


def test_unknown_comment_delete_is_not_found(client, alice_headers):
    res = client.delete(
        "/api/comments/99999999-9999-4999-8999-999999999999", headers=alice_headers
    )
    assert res.status_code == 404
