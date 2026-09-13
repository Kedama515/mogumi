from datetime import date

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)


class FridgeItem(Base):
    __tablename__ = "fridge_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    added_date = Column(Date, nullable=False, default=date.today)
    memo = Column(String, default="")


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    memo = Column(String, default="")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True)
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

    meal = relationship("Meal", back_populates="dishes")


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
