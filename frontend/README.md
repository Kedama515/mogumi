# mogumi frontend

mogumiのWeb UI(Vite + React + TypeScript)。バックエンド([`../backend`](../backend))のAPIをタブで叩く単一ページアプリ。

## セットアップ・起動

事前にバックエンドを起動しておくこと(`../backend/README.md`参照、`http://127.0.0.1:8000`で待ち受け)。

    npm install
    npm run dev

`http://localhost:5173` を開く。`/api` へのリクエストは `vite.config.ts` の `server.proxy` 設定でバックエンドへ転送される。

## 画面構成

未ログイン時はログイン画面のみ表示される(`POST /api/auth/login`)。ログイン成功時に受け取ったJWTを`localStorage`に保存し、以後のAPIリクエストに`Authorization: Bearer`ヘッダーとして付与する。401が返ってきたら自動的にトークンを破棄してログイン画面に戻す。

ログイン後は画面下部に5つのタブ(モバイルアプリ風の固定ナビ)を常時表示する。最重要機能の「献立」は中央に円形の強調ボタンとして配置している。

| タブ(左から) | 役割 | 対応API |
|---|---|---|
| 冷蔵庫 | 「冷蔵庫」「常備品」のサブタブ切り替え。それぞれ一覧・追加・削除。冷蔵庫は野菜/肉/魚介などカテゴリごとにグルーピング表示 | `GET/POST/DELETE /api/fridge`, `/api/pantry` |
| レシピ | お気に入りレシピの一覧・詳細(材料・手順)・追加・削除 | `GET/POST/DELETE /api/recipes` |
| **献立**(中央・円形強調) | フォーム(食事・人数・直近日数・希望)を送って献立全体の提案を受け取り、気に入ったら記録する | `POST /api/suggestions`, `POST /api/meals` |
| カレンダー | 直近N日分の献立記録の一覧(名称のみカレンダー、中身は一覧表示。本格的なカレンダーUIは今後) | `GET /api/meals` |
| ホーム | 右上の⚙️から設定(バージョン情報・主要ライブラリ一覧・ログアウト)に遷移 | - |

設定はホームタブに含まれるため下部タブには出てこない(`tab==='settings'`のとき、ホームがアクティブ表示になる)。ログインユーザーの作成は`backend`側の`scripts/create_user.py`から行う(このアプリに登録画面はない)。

画面下部の固定タブナビのすぐ上に、小さく薄い字で「今回の費用」と「累計(このブラウザの`localStorage`に保存、USD)」を表示する。献立タブで提案を呼ぶたびに`api_usage.cost_usd`で両方を更新する(タブをまたいでも常時表示)。

## ディレクトリ構成

- `src/api.ts` — バックエンドAPIの呼び出し関数・認証トークンの保持・API利用料累計の記録をまとめたクライアント
- `src/types.ts` — バックエンドのPydanticスキーマに対応するTypeScript型
- `src/pages/` — タブごとの画面コンポーネント(`LoginPage`, `HomePage`, `SettingsPage`含む)。`FridgeManagementPage`が「冷蔵庫」「常備品」のサブタブをまとめる
- `src/components/CostFooter.tsx` — 画面下部のAPI利用料表示
- `src/App.tsx` — ログイン状態の管理と下部固定タブナビ(中央の円形ボタン含む)の入れ物

## ビルド

    npm run build

`tsc -b`(型チェック)→`vite build`の順で実行され、`dist/`に出力される。

## 未実装 / 次にやること

- 本番ビルドの配信方法(現状はVite dev serverでの動作のみ確認済み)
