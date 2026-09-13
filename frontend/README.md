# mogumi frontend

mogumiのWeb UI(Vite + React + TypeScript)。バックエンド([`../backend`](../backend))のAPIをタブで叩く単一ページアプリ。

## セットアップ・起動

事前にバックエンドを起動しておくこと(`../backend/README.md`参照、`http://127.0.0.1:8000`で待ち受け)。

    npm install
    npm run dev

`http://localhost:5173` を開く。`/api` へのリクエストは `vite.config.ts` の `server.proxy` 設定でバックエンドへ転送される。

## 画面構成

未ログイン時はログイン画面のみ表示される(`POST /api/auth/login`)。ログイン成功時に受け取ったJWTを`localStorage`に保存し、以後のAPIリクエストに`Authorization: Bearer`ヘッダーとして付与する。401が返ってきたら自動的にトークンを破棄してログイン画面に戻す。

| タブ | 役割 | 対応API |
|---|---|---|
| 献立提案 | フォーム(食事・人数・直近日数・希望)を送って献立全体の提案を受け取り、気に入ったら記録する | `POST /api/suggestions`, `POST /api/meals` |
| 冷蔵庫 | 冷蔵庫の中身の一覧・追加・削除 | `GET/POST/DELETE /api/fridge` |
| 常備品 | 常備品の一覧・追加・削除 | `GET/POST/DELETE /api/pantry` |
| レシピ | お気に入りレシピの一覧・詳細(材料・手順)・追加・削除 | `GET/POST/DELETE /api/recipes` |
| 履歴 | 直近N日分の献立記録の一覧 | `GET /api/meals` |

ログインユーザーの作成は`backend`側の`scripts/create_user.py`から行う(このアプリに登録画面はない)。

画面下部に小さく薄い字でClaude API利用料の累計(このブラウザの`localStorage`に保存、USD)を表示する。献立提案を呼ぶたびに`api_usage.cost_usd`を加算していく(タブをまたいでも常時表示)。

## ディレクトリ構成

- `src/api.ts` — バックエンドAPIの呼び出し関数・認証トークンの保持・API利用料累計の記録をまとめたクライアント
- `src/types.ts` — バックエンドのPydanticスキーマに対応するTypeScript型
- `src/pages/` — タブごとの画面コンポーネント(`LoginPage`含む)
- `src/components/CostFooter.tsx` — 画面下部のAPI利用料表示
- `src/App.tsx` — ログイン状態の管理とタブ切り替えの入れ物

## ビルド

    npm run build

`tsc -b`(型チェック)→`vite build`の順で実行され、`dist/`に出力される。

## 未実装 / 次にやること

- 本番ビルドの配信方法(現状はVite dev serverでの動作のみ確認済み)
