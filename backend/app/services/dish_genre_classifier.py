"""料理名からざっくりしたジャンル(カレー/丼/シチュー など)を解決する。

キーマカレーもバターチキンカレーもほうれん草カレーも「カレー」というくくりで
扱いたい、という要望から、食材カテゴリ分け(ingredient_categorizer.py)と同じ
「マスター+表記揺れ+未知はLLM1回だけ分類してキャッシュ」パターンを流用する。

`dish_genres`(正規化した料理名+ジャンル)と`dish_genre_aliases`(表記揺れ→
正規化料理名)の2テーブルをマスターとして使い、全household共通でキャッシュする。
献立の被り回避判定(「カレーが続いている」の検出)に使う想定。
"""

from sqlalchemy.orm import Session

from .. import models
from .claude_client import DISH_GENRE_VOCAB, classify_dish_genre


def resolve_genre(db: Session, dish_name: str) -> str:
    """料理名からジャンルを解決する。未知の料理名はLLMで1回だけ分類しマスターにキャッシュする。"""
    dish_name = dish_name.strip()

    alias_row = (
        db.query(models.DishGenreAlias).filter(models.DishGenreAlias.alias == dish_name).first()
    )
    if alias_row is not None:
        return alias_row.dish.genre

    result = classify_dish_genre(dish_name)
    canonical_name = result["canonical_name"]
    genre = result["genre"]
    if genre not in DISH_GENRE_VOCAB:
        genre = "その他"

    dish = (
        db.query(models.DishGenre)
        .filter(models.DishGenre.canonical_name == canonical_name)
        .first()
    )
    if dish is None:
        dish = models.DishGenre(canonical_name=canonical_name, genre=genre)
        db.add(dish)
        db.flush()
        db.add(models.DishGenreAlias(alias=canonical_name, dish_genre_id=dish.id))
        db.flush()

    # canonical_name が dish_name と同じ場合、上のself-aliasで既に登録済みなので二重登録しない
    already_aliased = (
        db.query(models.DishGenreAlias).filter(models.DishGenreAlias.alias == dish_name).first()
    )
    if already_aliased is None:
        db.add(models.DishGenreAlias(alias=dish_name, dish_genre_id=dish.id))

    db.commit()
    return dish.genre
