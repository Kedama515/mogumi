from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def build_prompt(
    db: Session,
    household_id: int,
    meal_type: str,
    servings: int,
    user_request: str,
    lookback_days: int,
) -> str:
    fridge = db.scalars(
        select(models.FridgeItem).where(models.FridgeItem.household_id == household_id)
    ).all()
    pantry = db.scalars(
        select(models.PantryItem).where(models.PantryItem.household_id == household_id)
    ).all()

    since = date.today() - timedelta(days=lookback_days)
    recent_meals = db.scalars(
        select(models.Meal)
        .where(models.Meal.household_id == household_id, models.Meal.date >= since)
        .order_by(models.Meal.date.desc())
    ).all()

    fridge_lines = "\n".join(f"- {i.name}" for i in fridge) or "(なし)"
    pantry_lines = "\n".join(f"- {i.name}" for i in pantry) or "(なし)"

    recent_lines = []
    for meal in recent_meals:
        dish_names = ", ".join(d.name for d in meal.dishes)
        tag_values = ", ".join(f"{t.category}:{t.value}" for t in meal.tags)
        recent_lines.append(f"- {meal.date} {meal.meal_type}: {dish_names} [{tag_values}]")
    recent_block = "\n".join(recent_lines) or "(記録なし)"

    return f"""あなたは家庭料理の献立提案アシスタントです。以下の情報をもとに、{servings}人前の{meal_type}の献立を提案してください。

# 冷蔵庫にある食材
{fridge_lines}

# 常備品(調味料・乾物など、常にある前提)
{pantry_lines}

# 直近{lookback_days}日間の献立(タンパク源・料理ジャンル・調理法が被らないようにすること)
{recent_block}

# ユーザーの希望
{user_request or "(特になし)"}

要件:
- 単品ではなく、主菜・副菜など献立全体を提案すること
- 冷蔵庫の食材を優先的に使うが、無理に全部使い切ろうとしなくてよい
- 直近の献立とタンパク源・料理ジャンル・調理法が偏らないようにすること
- 1人あたりたんぱく質をしっかり摂れる構成を意識すること(1日60g目標の一部として)
- propose_menu ツールを使って構造化データで回答すること
"""
