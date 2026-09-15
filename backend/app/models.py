from datetime import date

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Household(Base):
    """データの共有スコープ(世帯)。個人利用時は1ユーザー=1世帯として自動作成する。"""

    __tablename__ = "households"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(Date, nullable=False, default=date.today)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)

    # 献立設定(個人の好み)。人数は世帯の事実に近いが、被り回避の許容度は明確に個人差があり、
    # 世帯=1ユーザーの現状ではどちらも個人設定に寄せておく方が素直(2026-09-15〜)。
    # 「世帯」は冷蔵庫・パントリー・レシピ・献立記録など実際に共有される在庫・記録のみを指す。
    default_servings = Column(Integer, nullable=False, default=2)
    default_lookback_days = Column(Integer, nullable=False, default=3)


class FridgeItem(Base):
    __tablename__ = "fridge_items"

    id = Column(Integer, primary_key=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="その他")
    added_date = Column(Date, nullable=False, default=date.today)
    memo = Column(String, default="")


class IngredientCategory(Base):
    """食材の分類マスター(全household共通)。表記揺れはIngredientAliasで吸収する。"""

    __tablename__ = "ingredient_categories"

    id = Column(Integer, primary_key=True)
    canonical_name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)  # 野菜/肉/魚介/卵・乳製品/主食/果物/その他

    aliases = relationship(
        "IngredientAlias", back_populates="ingredient", cascade="all, delete-orphan"
    )


class IngredientAlias(Base):
    """食材名の表記揺れ(カタカナ/漢字/送り仮名など) → 正規化食材のマッピング。"""

    __tablename__ = "ingredient_aliases"

    id = Column(Integer, primary_key=True)
    alias = Column(String, nullable=False, unique=True)
    ingredient_id = Column(Integer, ForeignKey("ingredient_categories.id"), nullable=False)

    ingredient = relationship("IngredientCategory", back_populates="aliases")


class PantryItem(Base):
    __tablename__ = "pantry_items"
    __table_args__ = (UniqueConstraint("household_id", "name"),)

    id = Column(Integer, primary_key=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="その他")
    memo = Column(String, default="")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String, nullable=False)  # 朝食 / 昼食 / 夕食
    servings = Column(Integer, nullable=False, default=2)
    estimated = Column(Boolean, nullable=False, default=True)
    memo = Column(String, default="")

    # 栄養・材料費は献立(1人前)単位。品ごとの内訳は持たない(ai-project/menuの運用に合わせる)
    calories_kcal = Column(Float)
    protein_g = Column(Float)
    fat_g = Column(Float)
    carb_g = Column(Float)
    cost_yen_per_serving = Column(Float)

    dishes = relationship("MealDish", back_populates="meal", cascade="all, delete-orphan")
    tags = relationship("MealTag", back_populates="meal", cascade="all, delete-orphan")


class MealDish(Base):
    __tablename__ = "meal_dishes"

    id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String)  # 主菜/副菜/汁物/主食 など。提案由来でない場合はNoneもあり得る
    recipe_id = Column(Integer, ForeignKey("recipes.id"))  # 対応するお気に入りレシピ(あれば)
    genre = Column(String)  # カレー/丼 など。dish_genre_classifierで料理名から自動判定してキャッシュ

    meal = relationship("Meal", back_populates="dishes")
    ingredients = relationship(
        "MealDishIngredient", back_populates="meal_dish", cascade="all, delete-orphan"
    )


class MealDishIngredient(Base):
    """メニュー(品目)が使った食材の参照。分量・切り方などの詳細は持たない(それはレシピ側)。"""

    __tablename__ = "meal_dish_ingredients"

    id = Column(Integer, primary_key=True)
    meal_dish_id = Column(Integer, ForeignKey("meal_dishes.id"), nullable=False)
    name = Column(String, nullable=False)

    meal_dish = relationship("MealDish", back_populates="ingredients")


class DishGenre(Base):
    """料理名→ジャンル(カレー/丼など)のマスター(全household共通)。表記揺れはDishGenreAliasで吸収する。"""

    __tablename__ = "dish_genres"

    id = Column(Integer, primary_key=True)
    canonical_name = Column(String, nullable=False, unique=True)
    genre = Column(String, nullable=False)

    aliases = relationship("DishGenreAlias", back_populates="dish", cascade="all, delete-orphan")


class DishGenreAlias(Base):
    """料理名の表記揺れ → 正規化した料理名(DishGenre)のマッピング。"""

    __tablename__ = "dish_genre_aliases"

    id = Column(Integer, primary_key=True)
    alias = Column(String, nullable=False, unique=True)
    dish_genre_id = Column(Integer, ForeignKey("dish_genres.id"), nullable=False)

    dish = relationship("DishGenre", back_populates="aliases")


class MealTag(Base):
    __tablename__ = "meal_tags"

    id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    category = Column(String, nullable=False)  # protein / cuisine / cooking_method / style
    value = Column(String, nullable=False)

    meal = relationship("Meal", back_populates="tags")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    dish_name = Column(String, nullable=False)
    source_url = Column(String, default="")
    ingredients = Column(String, nullable=False)  # JSON-encoded list
    steps = Column(String, nullable=False)  # JSON-encoded list
    memo = Column(String, default="")

    tags = relationship("RecipeTag", back_populates="recipe", cascade="all, delete-orphan")


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    category = Column(String, nullable=False)  # protein / cuisine / cooking_method / style
    value = Column(String, nullable=False)

    recipe = relationship("Recipe", back_populates="tags")
