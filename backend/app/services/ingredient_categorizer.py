"""食材・食品名からカテゴリ(野菜/肉/魚介/調味料/油 など)を解決する。

冷蔵庫(fridge_items)・常備品(pantry_items)の両方から使う共通ロジック。
`ingredient_categories`(正規化名+カテゴリ)と`ingredient_aliases`(表記揺れ
→正規化食材)の2テーブルをマスターとして使い、全household共通でキャッシュする。

1. まずSEED_INGREDIENTSで一般的な食材・調味料+よくある表記揺れを起動時に
   登録しておく(LLM不要)
2. 未知の表記だけ、Claude(Haiku)に正規化名+カテゴリを1回だけ判定させ、
   結果をマスターに保存する(次回以降は誰の冷蔵庫・パントリーでも即ヒットする)
"""

from sqlalchemy.orm import Session

from .. import models
from .claude_client import CATEGORY_VOCAB, classify_ingredient

# (正規化名, カテゴリ, よくある表記揺れのリスト)
SEED_INGREDIENTS: list[tuple[str, str, list[str]]] = [
    ("にんじん", "野菜", ["ニンジン", "人参", "人蔘"]),
    ("たまねぎ", "野菜", ["玉ねぎ", "タマネギ", "玉葱"]),
    ("じゃがいも", "野菜", ["ジャガイモ", "馬鈴薯"]),
    ("キャベツ", "野菜", ["きゃべつ"]),
    ("だいこん", "野菜", ["大根", "ダイコン"]),
    ("はくさい", "野菜", ["白菜", "ハクサイ"]),
    ("こまつな", "野菜", ["小松菜", "コマツナ"]),
    ("ほうれんそう", "野菜", ["ほうれん草", "ホウレンソウ"]),
    ("ねぎ", "野菜", ["長ねぎ", "長ネギ", "ネギ", "葱"]),
    ("かぼちゃ", "野菜", ["南瓜", "カボチャ"]),
    ("なす", "野菜", ["ナス", "茄子"]),
    ("トマト", "野菜", ["とまと", "蕃茄", "ミニトマト"]),
    ("きゅうり", "野菜", ["キュウリ", "胡瓜"]),
    ("ピーマン", "野菜", ["ぴーまん"]),
    ("もやし", "野菜", ["モヤシ"]),
    ("しめじ", "野菜", ["シメジ"]),
    ("まいたけ", "野菜", ["舞茸", "マイタケ"]),
    ("しいたけ", "野菜", ["椎茸", "シイタケ"]),
    ("かぶ", "野菜", ["カブ", "蕪", "かぶ(葉付き)"]),
    ("さつまいも", "野菜", ["サツマイモ", "薩摩芋"]),
    ("さといも", "野菜", ["里芋", "サトイモ"]),
    ("にんにく", "野菜", ["ニンニク", "大蒜"]),
    ("しょうが", "野菜", ["生姜", "ショウガ"]),
    ("レタス", "野菜", ["れたす"]),
    ("ブロッコリー", "野菜", []),
    ("かいわれ大根", "野菜", ["かいわれ", "カイワレ大根"]),
    ("豚肉", "肉", ["ぶたにく", "豚小間切れ", "豚こま", "豚バラ"]),
    ("鶏肉", "肉", ["とりにく", "鶏もも", "鶏むね"]),
    ("鶏ひき肉", "肉", ["とりひきにく", "鶏挽き肉"]),
    ("牛肉", "肉", ["ぎゅうにく"]),
    ("ひき肉", "肉", ["挽き肉", "ミンチ"]),
    ("ベーコン", "肉", []),
    ("生ハム", "肉", ["なまはむ"]),
    ("ウインナー", "肉", ["ウィンナー", "ソーセージ"]),
    ("ぶり", "魚介", ["鰤", "ブリ"]),
    ("さけ", "魚介", ["鮭", "サケ", "シャケ"]),
    ("さば", "魚介", ["鯖", "サバ"]),
    ("まぐろ", "魚介", ["鮪", "マグロ"]),
    ("えび", "魚介", ["海老", "エビ"]),
    ("いか", "魚介", ["烏賊", "イカ"]),
    ("ツナ缶", "魚介", ["つな缶", "ツナ油漬け"]),
    ("たまご", "卵・乳製品", ["卵", "玉子", "タマゴ"]),
    ("牛乳", "卵・乳製品", ["ぎゅうにゅう", "ミルク"]),
    ("チーズ", "卵・乳製品", ["ちーず", "ゴーダチーズ"]),
    ("ヨーグルト", "卵・乳製品", []),
    ("バター", "卵・乳製品", []),
    ("油あげ", "卵・乳製品", ["油揚げ", "アブラアゲ"]),
    ("豆腐", "卵・乳製品", ["とうふ"]),
    ("ご飯", "主食", ["米", "白米", "ライス"]),
    ("パン", "主食", ["ぱん"]),
    ("うどん", "主食", []),
    ("そば", "主食", ["蕎麦"]),
    ("パスタ", "主食", ["スパゲッティ"]),
    ("りんご", "果物", ["リンゴ", "林檎"]),
    ("バナナ", "果物", ["ばなな"]),
    ("みかん", "果物", ["ミカン", "蜜柑"]),
    # 常備品(パントリー)向け
    ("醤油", "調味料", ["しょうゆ", "しょう油"]),
    ("砂糖", "調味料", ["さとう"]),
    ("塩", "調味料", ["しお"]),
    ("胡椒", "調味料", ["こしょう", "コショウ"]),
    ("塩胡椒", "調味料", ["塩こしょう", "しおこしょう"]),
    ("味噌", "調味料", ["みそ"]),
    ("酢", "調味料", ["す"]),
    ("片栗粉", "調味料", ["かたくりこ"]),
    ("味の素", "調味料", ["味の素(うま味調味料)"]),
    ("鶏ガラ", "調味料", ["鶏がら", "鶏ガラスープの素"]),
    ("コンソメ", "調味料", []),
    ("レモンジュース", "調味料", ["レモン汁"]),
    ("オイスターソース", "調味料", []),
    ("ウスターソース", "調味料", []),
    ("XO醤", "調味料", []),
    ("コチュジャン", "調味料", []),
    ("甜麺醤", "調味料", []),
    ("豆板醤", "調味料", []),
    ("マスタード", "調味料", []),
    ("わさび", "調味料", ["ワサビ", "山葵"]),
    ("鷹の爪", "調味料", ["たかのつめ", "唐辛子"]),
    ("パセリ", "調味料", ["乾燥パセリ"]),
    ("カレールー", "調味料", ["カレー粉"]),
    ("シチュールー(ホワイト)", "調味料", ["シチュールー", "ホワイトシチュールー"]),
    ("シチュールー(ビーフ)", "調味料", ["ビーフシチュールー"]),
    ("ごま", "調味料", ["ゴマ", "胡麻"]),
    ("サラダ油", "油", []),
    ("胡麻油", "油", ["ごま油"]),
    ("オリーブオイル", "油", []),
    ("鯖缶", "魚介", ["さば缶"]),
    ("味噌汁の具", "乾物・缶詰", []),
    ("春雨", "乾物・缶詰", []),
    ("麩", "乾物・缶詰", ["ふ"]),
    ("わかめ", "乾物・缶詰", ["ワカメ"]),
    ("コーン缶", "乾物・缶詰", []),
    ("トマト缶", "乾物・缶詰", []),
]


def seed_ingredient_master(db: Session) -> None:
    """アプリ起動時に呼ぶ想定。既存の正規化名はスキップするので何度でも安全。"""
    for canonical_name, category, aliases in SEED_INGREDIENTS:
        ingredient = (
            db.query(models.IngredientCategory)
            .filter(models.IngredientCategory.canonical_name == canonical_name)
            .first()
        )
        if ingredient is None:
            ingredient = models.IngredientCategory(canonical_name=canonical_name, category=category)
            db.add(ingredient)
            db.flush()
            db.add(models.IngredientAlias(alias=canonical_name, ingredient_id=ingredient.id))

        for alias in aliases:
            exists = (
                db.query(models.IngredientAlias).filter(models.IngredientAlias.alias == alias).first()
            )
            if exists is None:
                db.add(models.IngredientAlias(alias=alias, ingredient_id=ingredient.id))
    db.commit()


def lookup_canonical_name(db: Session, name: str) -> str:
    """食材名をエイリアスマスターだけを見て正規化する(LLM呼び出しはしない)。
    未知の表記はそのまま返す(#33: 冷蔵庫/パントリーとのマッチング用、キャッシュ登録は行わない)。"""
    name = name.strip()
    alias_row = db.query(models.IngredientAlias).filter(models.IngredientAlias.alias == name).first()
    return alias_row.ingredient.canonical_name if alias_row is not None else name


def resolve_category(db: Session, name: str) -> str:
    """食材名からカテゴリを解決する。未知の表記はLLMで1回だけ分類しマスターにキャッシュする。"""
    name = name.strip()

    alias_row = db.query(models.IngredientAlias).filter(models.IngredientAlias.alias == name).first()
    if alias_row is not None:
        return alias_row.ingredient.category

    result = classify_ingredient(name)
    canonical_name = result["canonical_name"]
    category = result["category"]
    if category not in CATEGORY_VOCAB:
        category = "その他"

    ingredient = (
        db.query(models.IngredientCategory)
        .filter(models.IngredientCategory.canonical_name == canonical_name)
        .first()
    )
    if ingredient is None:
        ingredient = models.IngredientCategory(canonical_name=canonical_name, category=category)
        db.add(ingredient)
        db.flush()
        db.add(models.IngredientAlias(alias=canonical_name, ingredient_id=ingredient.id))
        db.flush()

    # canonical_name が name と同じ場合、上のself-aliasで既に登録済みなので二重登録しない
    already_aliased = (
        db.query(models.IngredientAlias).filter(models.IngredientAlias.alias == name).first()
    )
    if already_aliased is None:
        db.add(models.IngredientAlias(alias=name, ingredient_id=ingredient.id))

    db.commit()
    return ingredient.category
