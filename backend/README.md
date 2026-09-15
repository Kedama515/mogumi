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
- `GET/POST/PUT/DELETE /api/fridge` — 冷蔵庫の中身。追加時に食材名から`category`(野菜/肉/魚介など)を自動判定して付与する(`docs/data-model.md`の`ingredient_categories`参照)。PUTは入庫日(`added_date`)の更新用
- `GET/POST/PUT/DELETE /api/pantry` — 常備品。冷蔵庫と同じマスターで`category`(調味料/油/乾物・缶詰など)を自動判定して付与する。PUTは在庫ステータス(`status`: たっぷり/そろそろ切れそう/切れた)の更新用
- `GET/POST/DELETE /api/meals` — 献立記録(取得は`days`で直近N日分、または`year`+`month`でその月1ヶ月分。下書き(`is_draft=true`)は一覧に出てこない)。栄養・材料費は献立(1人前)単位で持つ。品目(`menu`)は名前+`role`(主菜/副菜など)+`recipe_id`(名前完全一致で自動リンク、任意)+`ingredients`(使用食材名のリスト)+`is_batch_cooked`(作り置きフラグ)を持つ。`genre`(カレー/丼など)は品目作成時に料理名から自動判定して付与する(`docs/data-model.md`の`dish_genres`参照)。`is_batch_cooked`がtrueの品目は同時に`fridge_items`へ自動登録される(category=「作り置き料理」)。DELETEは下書きの破棄などに使う
- `GET /api/meals/status?date=&meal_type=` — 指定スロットの確定済み献立(`confirmed_meal`)・下書き(`draft_for_slot`)の有無と、household全体で放置されている過去の下書き(`stale_draft`)の有無を返す(#37・#38)。献立提案フォームはこれを見て、放置下書きがあれば新規提案をブロックし、同じスロットに下書きがあればそれを再表示し、確定済みなら警告バナーを出す
- `POST /api/meals/{id}/confirm` — 献立提案の下書きを正式な献立として確定する(`is_draft`をfalseにする)。body(任意)で`batch_cooked_dish_names`(作り置きにする品目名のリスト)を渡せる
- `GET /api/meals/{id}/consumable` — 献立が使った食材から、冷蔵庫・パントリーの消費済み候補(`fridge_candidates`/`pantry_candidates`)を返す(#33)。食材名は`ingredient_aliases`で正規化してマッチングする
- `POST /api/meals/{id}/consume` — 冷蔵庫食材の削除・パントリー在庫ステータスの更新をまとめて行う(`fridge_item_ids`, `pantry_updates`)。完全自動ではなく、`consumable`で提示した候補をユーザーが確認・選択したものだけを反映する半自動設計
- `POST /api/meals/dishes/{meal_dish_id}/favorite` — メニュー(品目)をお気に入り登録してレシピ化する(#19)。既にレシピ紐付け済みならそれを返す(冪等)。メニュー自体は編集しない、生成されたレシピは`PUT /api/recipes/{id}`で後から編集する想定
- `GET/POST/PUT/DELETE /api/recipes`, `GET /api/recipes/{id}` — お気に入りレシピ(材料・手順・タグ)。PUTで既存レシピの全項目を更新できる
- `GET/PUT /api/settings` — 個人設定(人数のデフォルト値、被り回避の段階別許容日数、献立提案モード)
- `POST /api/suggestions` — 献立提案。`target_date`(デフォルト今日、未来日付も指定可)・`cuisine_preference`(和洋中の明示指定、省略時はおまかせ)・冷蔵庫・常備品・段階別被り回避(`docs/data-model.md`の`users.avoid_days_*`参照)を踏まえて、Claude APIに複数品の献立+調理タイムライン+各品目の使用食材を提案させる。`current_menu`+`refinement_request`を渡すと、直前の提案をベースにステートレスに微調整できる(会話履歴は持たない)。生成結果は(household, target_date, meal_type)スロットの下書きとして即座に`meals`へ保存され(同じスロットへの再提案・微調整は上書き)、レスポンスの`meal_id`を使って`POST /api/meals/{id}/confirm`で確定する想定。呼び出すたびに使用トークン数と概算費用(USD)をサーバーの標準出力にログする(`app/services/claude_client.py`の料金表は手動更新、モデルを変えたら追記すること)

## 既存データの移行

`ai-project/menu/data/`(fridge.csv, pantry.csv, meals.json)の内容を取り込むスクリプト:

    python3 -m scripts.migrate_from_menu_project [username]

`ai-project/menu/recipes/*.md`(YAMLフロントマター付きMarkdown)の内容を取り込むスクリプト:

    python3 -m scripts.migrate_recipes [username]

どちらも`username`で指定したユーザーのhousehold宛に取り込む(省略時、DBにユーザーが1人だけならそのユーザー宛。複数いる場合は指定必須)。対象householdのデータを一度全削除してから取り込み直すため、何度でも再実行可能。menuプロジェクト側のデータを更新したら再実行して同期する運用。

Web UIは [`../frontend`](../frontend) を参照。
