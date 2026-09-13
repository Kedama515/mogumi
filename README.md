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
cp .env.example .env  # ANTHROPIC_API_KEY を設定
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
```

## 構成

```
mogumi/
├── backend/   FastAPI + SQLite。詳細は backend/README.md
└── frontend/  Vite + React + TypeScript。詳細は frontend/README.md
```

## 実装状況(2026-09-14時点)

| 機能 | 状態 |
|---|---|
| 冷蔵庫・常備品の管理(一覧/追加/削除) | ✅ backend/frontend とも実装済み |
| 既存データ(`ai-project/menu`)の移行スクリプト | ✅ 実装済み、実データで動作確認済み |
| 献立提案(冷蔵庫・履歴を踏まえてClaude APIが献立全体+調理タイムラインを提案) | ✅ backend実装済み・frontend実装済み。ダミーキーでのエラーハンドリングは確認済みだが、実際のAPIキーでの成功パスは未確認 |
| 献立記録・履歴閲覧 | ✅ backend/frontend とも実装済み |
| レシピ管理 | ❌ 未着手(テーブルのみ用意) |
| 認証 | ❌ 未着手(個人利用のみ想定) |
| iOSアプリ | ❌ 未着手(将来的な目標。API構成にしているのはこれを見据えているため) |

## 運用の元になっているプロジェクトとの関係

これまでClaudeとの会話ベース+CSV/JSONで運用してきた `ai-project/menu` の「冷蔵庫在庫→献立提案→記録→レシピ化→スマホ用HTML」というフローをアプリ化したもの。運用フローやデータ構造の背景は `ai-memory/facts/mogumi-project.md`, `ai-memory/facts/menu-project.md` を参照。
