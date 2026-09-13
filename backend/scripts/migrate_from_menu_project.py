"""ai-project/menu の CSV/JSON データを mogumi の SQLite DB に取り込む。

実行方法(backend/ ディレクトリから):

    python3 -m scripts.migrate_from_menu_project

対象: data/fridge.csv, data/pantry.csv, data/meals.json
既存の fridge_items / pantry_items / meals を全て削除してから取り込み直す
(何度でも安全に再実行できるようにするため。recipes テーブルは対象外)。
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402

MENU_DATA_DIR = BACKEND_DIR.parent.parent / "menu" / "data"


def migrate_fridge(db, csv_path: Path) -> int:
    count = 0
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(
                models.FridgeItem(
                    name=row["食材"],
                    added_date=date.fromisoformat(row["追加日"]),
                    memo=row.get("メモ") or "",
                )
            )
            count += 1
    return count


def migrate_pantry(db, csv_path: Path) -> int:
    count = 0
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.add(models.PantryItem(name=row["食材"], memo=row.get("メモ") or ""))
            count += 1
    return count


def migrate_meals(db, json_path: Path) -> int:
    with json_path.open(encoding="utf-8") as f:
        meals = json.load(f)

    for meal in meals:
        nutrition = meal.get("nutrition_per_serving") or {}
        db_meal = models.Meal(
            date=date.fromisoformat(meal["date"]),
            meal_type=meal["meal_type"],
            servings=meal["servings"],
            estimated=meal.get("estimated", True),
            memo=meal.get("memo") or "",
            calories_kcal=nutrition.get("calories_kcal"),
            protein_g=nutrition.get("protein_g"),
            fat_g=nutrition.get("fat_g"),
            carb_g=nutrition.get("carb_g"),
            cost_yen_per_serving=meal.get("cost_yen_per_serving"),
        )
        for dish_name in meal.get("menu", []):
            db_meal.dishes.append(models.MealDish(name=dish_name))
        for category, values in (meal.get("tags") or {}).items():
            for value in values:
                db_meal.tags.append(models.MealTag(category=category, value=value))
        db.add(db_meal)
    return len(meals)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.MealTag).delete()
        db.query(models.MealDish).delete()
        db.query(models.Meal).delete()
        db.query(models.FridgeItem).delete()
        db.query(models.PantryItem).delete()
        db.commit()

        fridge_count = migrate_fridge(db, MENU_DATA_DIR / "fridge.csv")
        pantry_count = migrate_pantry(db, MENU_DATA_DIR / "pantry.csv")
        meals_count = migrate_meals(db, MENU_DATA_DIR / "meals.json")
        db.commit()

        print(f"fridge_items: {fridge_count}")
        print(f"pantry_items: {pantry_count}")
        print(f"meals: {meals_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
