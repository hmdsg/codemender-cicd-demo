"""外部 HTTP アクセスの共通ヘルパ。

社内規約: **外部から与えられた URL を取得する処理は必ず `fetch_external()` を経由すること。**
`requests.get()` を直接呼んではならない。

`fetch_external()` は以下を強制する:
  - スキームは http / https のみ
  - 名前解決した IP がプライベート・ループバック・リンクローカル・予約済みレンジでないこと
    (クラウドのメタデータサーバ 169.254.169.254 はリンクローカルとして弾かれる)
  - リダイレクト追従の禁止（リダイレクト先で内部に回り込むのを防ぐ）
  - タイムアウトと最大レスポンスサイズの設定
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import requests

ALLOWED_SCHEMES = frozenset({"http", "https"})
DEFAULT_TIMEOUT_SECONDS = 5
MAX_RESPONSE_BYTES = 1 * 1024 * 1024


class BlockedRequestError(ValueError):
    """要求された URL が社内ポリシーで禁止されている。"""


def _resolved_addresses(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """ホスト名を解決し、得られた全ての IP アドレスを返す。"""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise BlockedRequestError(f"cannot resolve host: {hostname}") from exc
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def assert_public_url(url: str) -> None:
    """URL が外部宛として安全でなければ BlockedRequestError を送出する。"""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise BlockedRequestError(f"scheme not allowed: {parsed.scheme!r}")

    if not parsed.hostname:
        raise BlockedRequestError("url has no host")

    for address in _resolved_addresses(parsed.hostname):
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local  # 169.254.0.0/16 (メタデータサーバ)
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise BlockedRequestError(f"destination is not a public address: {address}")


def fetch_external(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> bytes:
    """外部 URL を安全に取得する。社外向け通信は必ずこの関数を使うこと。"""
    assert_public_url(url)
    response = requests.get(
        url,
        timeout=timeout,
        allow_redirects=False,
        stream=True,
    )
    response.raise_for_status()
    return response.raw.read(MAX_RESPONSE_BYTES, decode_content=True)


def post_external(url: str, payload: dict, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> int:
    """外部 URL へ安全に POST する。社外向け通信は必ずこの関数を使うこと。"""
    assert_public_url(url)
    response = requests.post(url, json=payload, timeout=timeout, allow_redirects=False)
    return response.status_code
