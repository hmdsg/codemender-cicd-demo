# CodeMender × GitHub Actions CI/CD ライブデモ

> **⚠️ 教育・デモ専用リポジトリ（デプロイ禁止）**
> 本リポジトリの `app/` および `native/` には、Google Cloud **CodeMender** の PR 差分スキャン（`cm find --diff`）および自動修正 PR 生成（`cm fix`）を実演するための意図的な脆弱性が含まれています。本番環境や公開サーバへは絶対にデプロイしないでください。

[公式ドキュメント: CI/CD との統合](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents/codemender/integrate-with-cicd?hl=ja) に準拠した **GitHub Web UI 完結型のライブデモ環境** です。

---

## デモの見どころ（3 つのポイント）

1. **秘密鍵レスの Google Cloud 連携（Workload Identity Federation）**
   * GitHub にサービスアカウント JSON キーを保存せず、OIDC トークンで Vertex AI / CodeMender API へ安全にアクセスします。
2. **PR 差分スキャン（`cm find --diff`）と既存負債の切り分け**
   * `app/reports.py` 等の既存コードには最初から脆弱性が残っていますが、それらは `[LEGACY / UNTOUCHED]` として分離され開発を止めません。
   * **今回の Pull Request が新たに混入させた脆弱性（ルールベース SAST が見逃すマルチテナント認可漏れ = IDOR）だけ** を 1〜2 分で検知してマージをブロックし、GitHub Code Scanning（`Files changed` タブ）の該当行にインライン警告を表示します。
3. **テスト検証済みの自動修正 PR（`CodeMender autofix`）**
   * スキャンが失敗すると自動で `autofix` ジョブが起動し、周辺コードの規約（`g.tenant_id`）に合わせた最小パッチを生成・単体テスト（`pytest` + AddressSanitizer）通過を確認したうえで、開発ブランチ宛てに修正 PR を自動作成します。

---

## ライブ実演手順（すべてブラウザ上の GitHub Web 操作のみ・約 6 分）

### Act 1：Web エディタで「テナント絞り込みを忘れた新 API」の PR を作成する【30 秒】

1. リポジトリ上の **[`app/comments.py`](app/comments.py)** を開き、右上の **✏️（Edit this file）** をクリックします。
2. ファイルの一番下に、以下のコードブロック（右上のコピーボタンでコピー可能）を貼り付けます。
   * 既存の `list_comments` や `delete_comment` では `AND tenant_id = ?` で自テナントに絞っていますが、この新 API だけうっかり `WHERE id = ?` のみにした典型的な実装ミス（他社コメントが読める IDOR）です。

```python


@bp.get("/api/comments/<comment_id>")
@require_auth
def get_comment(comment_id: str):
    """指定 ID のコメント詳細を返す。"""
    conn = db.connect(current_app.config["DB_PATH"])
    try:
        row = conn.execute(
            "SELECT id, report_id, author_id, body FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(dict(row)), 200
```

3. **Commit changes...** をクリックし、**「Create a new branch for this commit and start a pull request」** を選んで **Propose changes** → **Create pull request** を押します。

---

### Act 2：`CodeMender scan` による検知とインライン警告の確認【約 1.5〜2 分】

1. PR 画面下部のチェック欄で **`CodeMender scan`** が自動実行され、`❌ Failing` になることを確認します。
2. **`CodeMender scan`** の詳細ログ（または Actions の **Summary** 画面）を開き、以下を確認します：
   * Workload Identity 連携による Google Cloud 認証と `cm find . --diff=origin/main` の実行
   * 新規追加した `get_comment` の IDOR（`MEDIUM`）のみがブロック対象となり、未変更ファイルの既存脆弱性は除外されていること
3. PR の **「Files changed」タブ** を開くと、今追加した SQL クエリ行の直下に **GitHub Code Scanning の警告アノテーション** が表示されます。

---

### Act 3：`CodeMender autofix` による修正 PR の自動到着【約 3〜4 分】

1. `CodeMender scan` の失敗を受けて、後続の **`CodeMender autofix`** ジョブが自動起動します。
2. 完了後、上部の **「Pull requests」タブ** を開くと、`github-actions[bot]` から **`CodeMender fixes for #<PR番号>`** という修正 PR が自動で届いています。

---

### Act 4：修正 PR を Web でレビュー＆マージ → 元 PR がグリーンに変わる【30 秒＋再検査 1 分】

1. 届いた修正 PR を開いて **「Files changed」** を見ると、`AND tenant_id = ?` と `(comment_id, g.tenant_id)` だけが最小差分で追加されています。
2. **「Merge pull request」** → **「Confirm merge」** をクリックして開発ブランチに取り込みます。
3. 元の新機能 PR に戻ると、ブランチ更新によって **`CodeMender scan` が自動で再実行** され、今度は **`✅ All checks have passed`** に変わり、安全に `main` へマージできる状態になります。
