# mogumi backend

FastAPI + SQLite backend for mogumi(冷蔵庫管理 → 献立提案 → レシピ管理 のアプリ化)。

## セットアップ

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env  # ANTHROPIC_API_KEY を設定

## 起動

    uvicorn app.main:app --reload

http://127.0.0.1:8000/docs で Swagger UI から動作確認できる。起動時に `mogumi.db`(SQLite)が自動生成される。

DBのテーブル定義・ER図は [`docs/data-model.md`](docs/data-model.md) を参照。

## エンドポイント(MVP)

- `GET/POST/DELETE /api/fridge` — 冷蔵庫の中身
- `GET/POST/DELETE /api/pantry` — 常備品
- `GET/POST /api/meals` — 献立記録(直近分の取得、新規記録)。栄養・材料費は献立(1人前)単位で持ち、品目は名前のみの配列(`menu`)
- `POST /api/suggestions` — 献立提案。冷蔵庫・常備品・直近N日の献立(タグ含む)を踏まえて、Claude APIに複数品の献立+調理タイムラインを提案させる。返ってきた提案が気に入ったら `POST /api/meals` で記録する想定(提案自体はDBに保存しない)

## 既存データの移行

`ai-project/menu/data/`(fridge.csv, pantry.csv, meals.json)の内容を取り込むスクリプト:

    python3 -m scripts.migrate_from_menu_project

fridge_items / pantry_items / meals を一度全削除してから取り込み直すため、何度でも再実行可能(recipesテーブルは対象外)。menuプロジェクト側のデータを更新したら再実行して同期する運用。

## 未実装 / 次にやること

- レシピ(recipes)のCRUD
- 認証(今のところ個人利用のみ想定のため未実装)

Web UIは [`../frontend`](../frontend) を参照。
