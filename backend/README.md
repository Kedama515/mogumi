# mogumi backend

FastAPI + SQLite backend for mogumi(冷蔵庫管理 → 献立提案 → レシピ管理 のアプリ化)。

## セットアップ

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    # .env を編集: ANTHROPIC_API_KEY と MOGUMI_SECRET_KEY(下記コマンドで生成)を設定
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"

ログインユーザーを作成する(公開の登録エンドポイントはないため、このスクリプトから作る)。新規ユーザーには専用のhousehold(世帯)が自動作成される:

    python3 -m scripts.create_user

## 起動

    uvicorn app.main:app --reload

http://127.0.0.1:8000/docs で Swagger UI から動作確認できる(右上の Authorize からログインすれば認証つきエンドポイントも試せる)。起動時に `mogumi.db`(SQLite)が自動生成される。

DBのテーブル定義・ER図は [`docs/data-model.md`](docs/data-model.md) を参照。

## エンドポイント(MVP)

`/api/auth/login` 以外は全てログイン必須(`Authorization: Bearer <token>`)。冷蔵庫・常備品・献立・レシピはすべて`household`(世帯)単位でスコープされており、同じ世帯に属さないユーザーからは見えない(データモデルは[`docs/data-model.md`](docs/data-model.md)参照)。

- `POST /api/auth/login` — ログイン(フォームエンコード、`username`/`password`)。JWTアクセストークンを返す(有効期限30日、個人利用のみ想定のため長め)
- `GET/POST/DELETE /api/fridge` — 冷蔵庫の中身。追加時に食材名から`category`(野菜/肉/魚介など)を自動判定して付与する(`docs/data-model.md`の`ingredient_categories`参照)
- `GET/POST/DELETE /api/pantry` — 常備品。冷蔵庫と同じマスターで`category`(調味料/油/乾物・缶詰など)を自動判定して付与する
- `GET/POST /api/meals` — 献立記録(直近分の取得、新規記録)。栄養・材料費は献立(1人前)単位で持ち、品目は名前のみの配列(`menu`)
- `GET/POST/DELETE /api/recipes`, `GET /api/recipes/{id}` — お気に入りレシピ(材料・手順・タグ)
- `POST /api/suggestions` — 献立提案。冷蔵庫・常備品・直近N日の献立(タグ含む)を踏まえて、Claude APIに複数品の献立+調理タイムラインを提案させる。返ってきた提案が気に入ったら `POST /api/meals` で記録する想定(提案自体はDBに保存しない)。呼び出すたびに使用トークン数と概算費用(USD)をサーバーの標準出力にログする(`app/services/claude_client.py`の料金表は手動更新、モデルを変えたら追記すること)

## 既存データの移行

`ai-project/menu/data/`(fridge.csv, pantry.csv, meals.json)の内容を取り込むスクリプト:

    python3 -m scripts.migrate_from_menu_project [username]

`ai-project/menu/recipes/*.md`(YAMLフロントマター付きMarkdown)の内容を取り込むスクリプト:

    python3 -m scripts.migrate_recipes [username]

どちらも`username`で指定したユーザーのhousehold宛に取り込む(省略時、DBにユーザーが1人だけならそのユーザー宛。複数いる場合は指定必須)。対象householdのデータを一度全削除してから取り込み直すため、何度でも再実行可能。menuプロジェクト側のデータを更新したら再実行して同期する運用。

Web UIは [`../frontend`](../frontend) を参照。
