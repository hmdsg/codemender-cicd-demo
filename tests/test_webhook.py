"""Webhook エンドポイントのテスト。

実際の外向き通信はしない。requests をモンキーパッチする。
"""

from __future__ import annotations

import pytest
import requests

from app import seed


class _FakeResponse:
    def __init__(self, text: str = "pong", ok: bool = True):
        self.text = text
        self.ok = ok


@pytest.fixture
def no_network(monkeypatch):
    """requests.get を差し替えて、呼ばれた URL を記録する。"""
    calls: list[str] = []

    def fake_get(url, *args, **kwargs):
        calls.append(url)
        return _FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def test_register_webhook(client, alice_headers, no_network):
    """★ 回帰ガード ★ 正当な外部 URL は登録できること。"""
    res = client.post(
        "/api/webhooks",
        headers=alice_headers,
        json={"callback_url": "https://hooks.example.com/acme"},
    )
    assert res.status_code == 201

    body = res.get_json()
    assert body["callback_url"] == "https://hooks.example.com/acme"
    assert body["reachable"] is True
    assert no_network == ["https://hooks.example.com/acme"]


def test_register_webhook_requires_url(client, alice_headers, no_network):
    res = client.post("/api/webhooks", headers=alice_headers, json={})
    assert res.status_code == 400


def test_register_webhook_requires_authentication(client):
    res = client.post("/api/webhooks", json={"callback_url": "https://hooks.example.com/x"})
    assert res.status_code == 401


def test_list_webhooks_is_tenant_scoped(client, alice_headers, bob_headers, no_network):
    client.post(
        "/api/webhooks", headers=alice_headers, json={"callback_url": "https://a.example.com/h"}
    )
    client.post(
        "/api/webhooks", headers=bob_headers, json={"callback_url": "https://b.example.com/h"}
    )

    alice_urls = [w["callback_url"] for w in client.get("/api/webhooks", headers=alice_headers).get_json()]
    bob_urls = [w["callback_url"] for w in client.get("/api/webhooks", headers=bob_headers).get_json()]

    assert alice_urls == ["https://a.example.com/h"]
    assert bob_urls == ["https://b.example.com/h"]


def test_seed_tokens_are_distinct():
    assert seed.TOKEN_ALICE != seed.TOKEN_BOB
