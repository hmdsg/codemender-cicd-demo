"""レポートエンドポイントの正常系テスト。

「修正によって壊してはいけない振る舞い」を定義する回帰ガード。
"""

from __future__ import annotations

from app import seed


def test_healthz(client):
    assert client.get("/healthz").status_code == 200


def test_get_own_report(client, alice_headers):
    res = client.get(f"/api/reports/{seed.REPORT_ACME}", headers=alice_headers)
    assert res.status_code == 200
    assert res.get_json()["title"] == "出張費 2026-07 大阪"


def test_get_report_of_other_tenant_is_not_found(client, alice_headers):
    """acme のユーザーは globex のレポートを取得できない。"""
    res = client.get(f"/api/reports/{seed.REPORT_GLOBEX}", headers=alice_headers)
    assert res.status_code == 404


def test_list_reports_is_tenant_scoped(client, alice_headers, bob_headers):
    alice_ids = {r["id"] for r in client.get("/api/reports", headers=alice_headers).get_json()}
    bob_ids = {r["id"] for r in client.get("/api/reports", headers=bob_headers).get_json()}

    assert alice_ids == {seed.REPORT_ACME, seed.REPORT_ACME_MEETING, seed.REPORT_ACME_SUPPLIES}
    assert bob_ids == {seed.REPORT_GLOBEX}


def test_requires_authentication(client):
    assert client.get("/api/reports").status_code == 401
    assert client.get("/api/reports", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_search_finds_own_report(client, alice_headers):
    res = client.get("/api/reports/search/by-title?q=出張", headers=alice_headers)
    assert res.status_code == 200
    assert [r["id"] for r in res.get_json()] == [seed.REPORT_ACME]


def test_search_is_tenant_scoped(client, alice_headers):
    """globex のレポート名で検索しても acme のユーザーには見えない。"""
    res = client.get("/api/reports/search/by-title?q=買収", headers=alice_headers)
    assert res.status_code == 200
    assert res.get_json() == []


def test_search_supports_descending_order(client, alice_headers):
    """order パラメータによる並び替えをサポートし続けること。

    ★ 回帰ガード ★
    ORDER BY の方向はプレースホルダ (?) にできない。SQL インジェクションを
    「全部プレースホルダに置き換える」だけで直そうとするとこのテストが落ちる。
    正しい修正は ASC / DESC の許可リスト検証である。
    """
    conn_res_asc = client.get(
        "/api/reports/search/by-title?q=&order=ASC", headers=alice_headers
    )
    conn_res_desc = client.get(
        "/api/reports/search/by-title?q=&order=DESC", headers=alice_headers
    )

    assert conn_res_asc.status_code == 200
    assert conn_res_desc.status_code == 200

    asc_titles = [r["title"] for r in conn_res_asc.get_json()]
    desc_titles = [r["title"] for r in conn_res_desc.get_json()]

    assert asc_titles == sorted(asc_titles)
    assert desc_titles == sorted(desc_titles, reverse=True)
