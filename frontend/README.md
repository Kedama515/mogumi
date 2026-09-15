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
| 冷蔵庫 | 「冷蔵庫」「常備品」のサブタブ切り替え。それぞれ一覧・追加・削除。どちらも野菜/肉/調味料/油などカテゴリごとにグルーピング表示(グループごとに開閉可能、`CategoryAccordion`コンポーネントを共用)。冷蔵庫の各アイテムは入庫日を、常備品の各アイテムは在庫ステータス(たっぷり/そろそろ切れそう/切れた)をその場で編集できる | `GET/POST/PUT/DELETE /api/fridge`, `GET/POST/PUT/DELETE /api/pantry` |
| レシピ | お気に入りレシピの一覧・詳細(材料・手順)・追加・編集・削除 | `GET/POST/PUT/DELETE /api/recipes` |
| **献立**(中央・円形強調) | フォーム(日付・食事・和洋中は常時表示、人数は普段は個人設定を使い折りたたみを開けば今回だけ上書き可能)を送って献立全体の提案をタイル表示で受け取り、微調整リクエストで再生成もできる。個人設定が「メニューを確認してから」モードなら、タイムラインは「この内容でタイムラインを見る」を押すまで隠される。品目ごとの「作り置き」チェックは記録時に冷蔵庫へ自動登録される。記録直後には使った食材を整理する`ConsumePanel`(冷蔵庫の消費済みチェック・パントリーのステータス変更をまとめて行える)と、品目ごとの「お気に入り登録」ボタンを表示する。放置された下書きがあれば新規提案をブロックし、同じスロットの下書きがあれば自動的に再表示、確定済みの献立があれば警告バナーを出す | `GET /api/settings`, `GET /api/meals/status`, `POST /api/suggestions`, `POST /api/meals/{id}/confirm`, `GET /api/meals/{id}/consumable`, `POST /api/meals/{id}/consume`, `POST /api/meals/dishes/{id}/favorite` |
| カレンダー | 月表示のカレンダーグリッド(日付ごとに朝食/昼食/夕食を色分けしたドットで表示)。前月/次月に移動でき、日付を選ぶと朝/昼/晩のタブ(夕食>昼食>朝食の優先順で初期選択)でその日の献立をメニューごとのタイルで表示。タイルを選ぶとジャンル・使用食材・お気に入り登録ボタンが下に表示される。LLM提案を経由せず直接手動で献立を追加することもでき、追加直後は`ConsumePanel`も表示される | `GET/POST /api/meals?year=&month=`, `POST /api/meals/dishes/{id}/favorite` |
| ホーム | 右上の⚙️から設定(個人設定・バージョン情報・主要ライブラリ一覧・アカウント)に遷移 | - |

設定はホームタブに含まれるため下部タブには出てこない(`tab==='settings'`のとき、ホームがアクティブ表示になる)。設定画面は「個人設定」(人数・献立提案モード・被り回避の段階別許容日数、`GET/PUT /api/settings`)と「アカウント」(ログアウト)にセクション分けしている。ログインユーザーの作成は`backend`側の`scripts/create_user.py`から行う(このアプリに登録画面はない)。

画面下部の固定タブナビのすぐ上に、小さく薄い字で「今回の費用」と「累計(このブラウザの`localStorage`に保存、USD)」を表示する。献立タブで提案を呼ぶたびに`api_usage.cost_usd`で両方を更新する(タブをまたいでも常時表示)。

## ディレクトリ構成

- `src/api.ts` — バックエンドAPIの呼び出し関数・認証トークンの保持・API利用料累計の記録をまとめたクライアント
- `src/types.ts` — バックエンドのPydanticスキーマに対応するTypeScript型
- `src/pages/` — タブごとの画面コンポーネント(`LoginPage`, `HomePage`, `SettingsPage`含む)。`FridgeManagementPage`が「冷蔵庫」「常備品」のサブタブをまとめる
- `src/components/CostFooter.tsx` — 画面下部のAPI利用料表示
- `src/components/ConsumePanel.tsx` — 献立記録直後に、使った食材の消費済みチェック(冷蔵庫)・在庫ステータス変更(パントリー)をまとめて行うパネル。SuggestPage/CalendarPageの両方から使う
- `src/App.tsx` — ログイン状態の管理と下部固定タブナビ(中央の円形ボタン含む)の入れ物

## ビルド

    npm run build

`tsc -b`(型チェック)→`vite build`の順で実行され、`dist/`に出力される。

## 未実装 / 次にやること

- 本番ビルドの配信方法(現状はVite dev serverでの動作のみ確認済み)
