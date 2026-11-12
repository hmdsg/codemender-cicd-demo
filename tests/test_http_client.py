"""社内共通ヘルパ app/common/http_client.py のテスト。

`fetch_external()` の SSRF 防御（プライベート/ループバック/リンクローカル宛ての
拒否・リダイレクト不追従・スキーム制限）を回帰ガードする。
DNS は monkeypatch でモックしており、ネットワークに依存しない。
"""

from __future__ import annotations

import socket

import pytest

from app.common import http_client

# テスト用の固定 DNS テーブル。
FAKE_DNS = {
    "metadata.google.internal": "169.254.169.254",
    "localhost": "127.0.0.1",
    "internal.corp.example": "10.0.0.5",
    "hooks.example.com": "93.184.216.34",
    "example.com": "93.184.216.34",
}


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    def fake_getaddrinfo(host, *args, **kwargs):
        if host in FAKE_DNS:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (FAKE_DNS[host], 0))]
        try:
            # IP リテラルはそのまま通す。
            socket.inet_aton(host)
        except OSError as exc:
            raise socket.gaierror(f"unknown host: {host}") from exc
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]

    monkeypatch.setattr(http_client.socket, "getaddrinfo", fake_getaddrinfo)


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/computeMetadata/v1/",  # GCP メタデータサーバ
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://127.0.0.1:8080/admin",
        "http://localhost/admin",
        "http://10.0.0.5/internal",
        "http://internal.corp.example/secrets",
        "http://192.168.1.1/",
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379/_INFO",
    ],
)
def test_blocks_internal_destinations(url):
    with pytest.raises(http_client.BlockedRequestError):
        http_client.assert_public_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://hooks.example.com/acme",
        "http://example.com:8080/hook",
        "https://93.184.216.34/hook",
    ],
)
def test_allows_public_destinations(url):
    """★ 回帰ガード ★ 正当な外部宛は通ること。過剰にブロックしない。"""
    http_client.assert_public_url(url)


def test_unresolvable_host_is_blocked():
    with pytest.raises(http_client.BlockedRequestError):
        http_client.assert_public_url("https://no-such-host.invalid/hook")
