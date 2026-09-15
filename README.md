# mogumi

冷蔵庫管理 → 献立提案(単品でなく献立全体) → レシピ管理 を一気通貫でアプリ化するプロジェクト。

- アーキテクチャ: バックエンド(FastAPI, SQLite) + フロント(将来的にiOSアプリ、まずはWebから着手)。フロントはAPI経由でバックエンドを叩く構成
- 最重要機能: 献立提案。ユーザーの希望を聞きつつ、冷蔵庫の中身・直近の献立との被りを踏まえて、単品でなく献立全体(主菜・副菜など)のレシピ・調理タイムラインをまとめて提案する
- 提案ロジックはバックエンドからClaude APIを呼び出して生成する

## クイックスタート

2つのターミナルでバックエンドとフロントエンドをそれぞれ起動する。

```bash
# ターミナル1: backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ANTHROPIC_API_KEY と MOGUMI_SECRET_KEY を設定
python3 -m scripts.create_user  # ログインユーザーを作成
uvicorn app.main:app --reload
```

```bash
# ターミナル2: frontend
cd frontend
npm install
npm run dev
```

`http://localhost:5173` を開く。API仕様は `http://127.0.0.1:8000/docs`(Swagger UI、FastAPIが自動生成)を参照。

初回は `ai-project/menu` の既存データ(冷蔵庫・常備品・献立履歴)を取り込んでおくと、献立提案がすぐ試せる:

```bash
cd backend && source .venv/bin/activate
python3 -m scripts.migrate_from_menu_project
python3 -m scripts.migrate_recipes
```

## 構成

```
mogumi/
├── backend/   FastAPI + SQLite。詳細は backend/README.md
└── frontend/  Vite + React + TypeScript。詳細は frontend/README.md
```

## 実装状況(2026-09-15時点)

| 機能 | 状態 |
|---|---|
| 冷蔵庫・常備品の管理(一覧/追加/削除) | ✅ backend/frontend とも実装済み。冷蔵庫は入庫日、常備品は在庫ステータス(たっぷり/そろそろ切れそう/切れた)をその場で編集可能(ブラウザ操作で確認済み) |
| 既存データ(`ai-project/menu`)の移行スクリプト | ✅ 実装済み、実データで動作確認済み |
| 献立提案(冷蔵庫・履歴を踏まえてClaude APIが献立全体+調理タイムラインを提案) | ✅ backend/frontend実装済み。実際のANTHROPIC_API_KEYでの成功パスも確認済み。未来日付・和洋中の明示指定・段階的な被り回避(料理名>ジャンル>調理法/タンパク源>和洋中)・微調整(ステートレス再生成)に対応(TestClient・ブラウザ操作で確認済み) |
| 献立記録・カレンダー閲覧 | ✅ backend/frontend とも実装済み。月表示グリッド+朝昼晩の色分けドット+日付選択でその日の献立をメニューごとのタイルで表示、選択するとジャンル・使用食材・お気に入り登録ボタンを表示。LLM提案を経由しない手動登録にも対応(ブラウザ操作で確認済み) |
| 認証(ユーザーログイン・JWT) | ✅ backend/frontend とも実装済み。ブラウザ操作で動作確認済み |
| マルチユーザーのデータ分離(household単位) | ✅ backend実装済み。2ユーザーでの分離をテストで確認済み。家族共有機能(招待UI)は未着手 |
| レシピ管理(一覧/詳細/追加/編集/削除、既存Markdownからの移行) | ✅ backend/frontend とも実装済み。献立の品目から「お気に入り登録」してレシピ化する動線も実装済み(ブラウザ操作で確認済み) |
| API利用料の可視化 | ✅ サーバーログ+画面フッター(今回/累計)実装済み |
| 献立設定(人数・献立提案モード・被り回避の段階別許容日数を個人設定として管理) | ✅ backend/frontend とも実装済み(TestClient・ブラウザ操作で動作確認済み) |
| メニューのジャンル分類(カレー/丼など、料理名から自動判定) | ✅ backend実装済み。被り回避ロジック(段階的粒度判定)で活用済み(TestClientで動作確認済み) |
| メニューの使用食材の参照(分量なし) | ✅ backend/frontend とも実装済み。献立提案が返す各品目の食材名を記録・表示(TestClientで動作確認済み) |
| 作り置きフラグ→冷蔵庫への自動登録 | ✅ backend/frontend とも実装済み。献立提案で「作り置き」にチェックした品目は確定時に冷蔵庫(category=作り置き料理)へ自動追加される(TestClientで動作確認済み) |
| 献立提案結果の下書き管理(タブ切り替え後も保持、放置下書きのブロック、重複記録の警告) | ✅ backend/frontend とも実装済み。提案生成時点で下書きとして保存し、確定するまでカレンダーには出ない。放置された過去の下書き・同じ枠の既存下書き・確定済み献立をそれぞれ検知してUIで案内する(TestClient・ブラウザ操作で動作確認済み) |
| 献立提案の微調整(ステートレス再生成)・メニュー確認モード | ✅ backend/frontend とも実装済み。微調整リクエストで直前の提案を上書き再生成できる。個人設定でモードを切り替えると、タイムラインの表示を「確認してから見る」形に変更できる(TestClient・ブラウザ操作で動作確認済み) |
| 献立記録後の食材消費・在庫更新(ワンタップ) | ✅ backend/frontend とも実装済み。献立記録直後に、使った食材を冷蔵庫から消費済みにする(候補は事前チェック済み)・使った常備品の在庫ステータスを変更する、をまとめて行えるパネルを表示(TestClient・ブラウザ操作で動作確認済み) |
| iOSアプリ | ❌ 未着手(将来的な目標。API構成にしているのはこれを見据えているため) |

## 運用の元になっているプロジェクトとの関係

これまでClaudeとの会話ベース+CSV/JSONで運用してきた `ai-project/menu` の「冷蔵庫在庫→献立提案→記録→レシピ化→スマホ用HTML」というフローをアプリ化したもの。運用フローやデータ構造の背景は `ai-memory/facts/mogumi-project.md`, `ai-memory/facts/menu-project.md` を参照。
