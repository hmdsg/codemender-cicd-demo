#!/usr/bin/env bash
#
# ビルド／テスト検証コマンド。
#
# ~/.codemender/config.yaml の build.command から呼ばれる。
# cm fix はパッチ適用後にこれを実行し、終了コード 0 を「機能退行なし」と判断する。
#
#   ./scripts/verify.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# cm fix の build.command はここから呼ばれる。「パッチが題材アプリを壊していないか」
# を判定するのが目的なので、対象は題材アプリのテストだけに絞る。
# CI 専用の tests/test_cm_*.py 等（配布 ZIP には同梱しない）を混ぜると、
# 教材と無関係な理由で cm fix の gate が赤くなってしまう。
APP_TESTS=(
  tests/test_attachments.py
  tests/test_reports.py
  tests/test_webhook.py
  tests/test_exporter.py
  tests/test_comments.py
  tests/test_http_client.py
)

echo "===== [verify] Python テスト (pytest) ====="
if command -v uv >/dev/null 2>&1; then
  uv run --no-sync pytest -q "${APP_TESTS[@]}"
else
  python3 -m pytest -q "${APP_TESTS[@]}"
fi

echo
echo "===== [verify] C テスト (AddressSanitizer) ====="
if command -v cc >/dev/null 2>&1 || command -v clang >/dev/null 2>&1; then
  make -C native test
else
  echo "[verify] C コンパイラが無いため native のテストをスキップします"
fi

echo
echo "===== [verify] すべて成功 ====="
