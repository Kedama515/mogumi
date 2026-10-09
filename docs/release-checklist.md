# 公開前チェックリスト

`.claude/agents/` のエージェント(`security-auditor`・`ops-readiness-reviewer`・`test-runner`)が、mogumi固有の基準としてこのファイルを読む。エージェント側は汎用の手順だけを持ち、判断基準はここに置く。

## セキュリティ(security-auditor)
- Claude APIのキーはバックエンドの環境変数のみ。フロントエンド・ビルド成果物・gitに含めない(Bedrock移行後はIAMロールでキー自体を不要にする)
- `/api/auth/login` 以外の全エンドポイントがJWT必須で、household_idで所有者を絞っている
- 公開前に全履歴を監査する(追跡ファイル/履歴の差分/認証情報/氏名・メール・IP/issueとコメント/実データの混入)。コミットのauthorはnoreplyアドレス、`Claude-Session:` トレーラーは付けない
- HTTPSを強制(HTTP→HTTPSリダイレクト、HSTS)。JWTの有効期限と保管方法を確認する
- 利用量の上限: ユーザーごとのレート制限と、AWS Budgets等の予算アラート。`POST /api/suggestions` がLLMを呼ぶ経路のため最優先
- サインアップ公開前に、レート制限(#47)と予算アラート(#53)が効いていること
- インフラ: EC2のセキュリティグループは80/443のみ公開、SSHは自分のIPのみ
- iOSアプリ化時: トークンはKeychainに保存し、端末に固定の秘密を埋め込まない

## 運用(ops-readiness-reviewer)
- ログはprintではなくloggingに(#48)。永続化し、パスワード・トークン・キーを出さない
- `MOGUMI_SECRET_KEY`・`ANTHROPIC_API_KEY` など必須環境変数が起動時に検証され、`backend/.env.example` が最新
- SQLite(EBS)のバックアップと復元手順がある。スキーマ変更は破壊的でないこと
- 予算アラートとCloudTrail監視(#53・#69)
- デプロイとロールバックの手順が `docs/aws-architecture.md` 等に再現可能な形である
- Claude API失敗・タイムアウト時に、利用者にわかるエラーメッセージが返る

## テスト(test-runner)
- フロントエンド: `npm run build`(型チェックを含む)、`npm run lint`
- バックエンド: 自動テストは未整備(2026-10時点)。未整備であることを毎回報告する
- 実データを書き換える `backend/scripts/migrate_*.py`・`create_user.py` と、実際にClaude APIを呼ぶ処理は実行しない

## テストの十分性(test-adequacy-reviewer)
- 優先して守るべき領域: 認証(未認証・期限切れトークン)、household_idによるデータ分離、被り回避ロジック(料理名・ジャンル・調理法/タンパク源・和洋中の粒度と許容日数)、献立の下書き(is_draft)の状態遷移(#38)
- 外部API: Claude API(`POST /api/suggestions`、食材・ジャンルの分類)の失敗・タイムアウト・不正なレスポンス時の挙動
- 過去に実際に困った不具合は回帰テストにする(例: 同じ料理名が連日提案される、作り置きは連日OK)
- テストは実データ(`mogumi.db`)と実際のClaude APIに依存させない(テスト用DB・モックを使う)
