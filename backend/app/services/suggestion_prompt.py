from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def build_prompt(
    db: Session,
    household_id: int,
    meal_type: str,
    servings: int,
    user_request: str,
    target_date: date,
    avoid_days_dish_name: int,
    avoid_days_genre: int,
    avoid_days_method_protein: int,
    avoid_days_cuisine: int,
    cuisine_preference: Optional[str] = None,
    current_menu: Optional[list[dict]] = None,
    refinement_request: str = "",
) -> str:
    fridge = db.scalars(
        select(models.FridgeItem).where(models.FridgeItem.household_id == household_id)
    ).all()
    pantry = db.scalars(
        select(models.PantryItem).where(models.PantryItem.household_id == household_id)
    ).all()

    max_lookback = max(
        avoid_days_dish_name, avoid_days_genre, avoid_days_method_protein, avoid_days_cuisine
    )
    since = target_date - timedelta(days=max_lookback)
    # 仮(下書き)の献立はまだ食べると決まっていないので被り回避の判定材料にしない(#38)
    recent_meals = db.scalars(
        select(models.Meal)
        .where(
            models.Meal.household_id == household_id,
            models.Meal.date >= since,
            models.Meal.date < target_date,
            models.Meal.is_draft.is_(False),
        )
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

    def within(days: int) -> list[models.Meal]:
        cutoff = target_date - timedelta(days=days)
        return [m for m in recent_meals if m.date >= cutoff]

    avoid_dish_names = sorted({d.name for m in within(avoid_days_dish_name) for d in m.dishes})
    avoid_genres = sorted(
        {d.genre for m in within(avoid_days_genre) for d in m.dishes if d.genre}
    )
    avoid_methods_proteins = sorted(
        {
            t.value
            for m in within(avoid_days_method_protein)
            for t in m.tags
            if t.category in ("protein", "cooking_method")
        }
    )
    avoid_cuisines = sorted(
        {t.value for m in within(avoid_days_cuisine) for t in m.tags if t.category == "cuisine"}
    )

    avoid_lines = [
        f"- 料理名(直近{avoid_days_dish_name}日): {', '.join(avoid_dish_names) or '(なし)'} → 同じ料理名は避ける",
        f"- ジャンル(直近{avoid_days_genre}日): {', '.join(avoid_genres) or '(なし)'} → 同じジャンルは避ける",
        f"- 調理法・タンパク源(直近{avoid_days_method_protein}日): {', '.join(avoid_methods_proteins) or '(なし)'} → 同じ調理法・タンパク源は避ける",
    ]
    if cuisine_preference:
        cuisine_line = f"- 和洋中: 今回は「{cuisine_preference}」の気分とのこと。直近の被りは気にせずこの方向で提案する"
    else:
        cuisine_line = (
            f"- 和洋中(直近{avoid_days_cuisine}日): {', '.join(avoid_cuisines) or '(なし)'}"
            " → 可能なら避けるが、他の条件を優先してよい(和洋中はおまかせでよい水準)"
        )
    avoid_lines.append(cuisine_line)
    avoid_block = "\n".join(avoid_lines)

    refine_block = ""
    if current_menu:
        current_lines = []
        for dish in current_menu:
            ingredients = "、".join(dish.get("ingredients") or [])
            current_lines.append(f"- {dish.get('role', '')} {dish['name']}({ingredients})")
        refine_block = f"""

# 現在の提案(これを微調整してほしい)
{chr(10).join(current_lines)}

# 微調整リクエスト
{refinement_request or "(特になし。全体的にもう少し良くして)"}

上記の現在の提案をベースに、微調整リクエストを反映した新しい提案を作成してください。冷蔵庫在庫・被り回避の制約は引き続き守ること。"""

    return f"""あなたは家庭料理の献立提案アシスタントです。以下の情報をもとに、{target_date}の{servings}人前の{meal_type}の献立を提案してください。

# 冷蔵庫にある食材
{fridge_lines}

# 常備品(調味料・乾物など、常にある前提)
{pantry_lines}

# 直近の献立(参考)
{recent_block}

# 被り回避(段階的な粒度。数字が小さいほど厳しく避けること)
{avoid_block}

# ユーザーの希望
{user_request or "(特になし)"}
{refine_block}

要件:
- 単品ではなく、主菜・副菜など献立全体を提案すること
- 冷蔵庫の食材を優先的に使うが、無理に全部使い切ろうとしなくてよい
- 上記の被り回避の指示に従うこと(料理名・ジャンル・調理法/タンパク源の順で優先的に避け、和洋中は柔軟でよい)
- 1人あたりたんぱく質をしっかり摂れる構成を意識すること(1日60g目標の一部として)
- 各品目(dish)ごとに、使う食材名(ingredients)を分量なしで具体的にリストアップすること
- propose_menu ツールを使って構造化データで回答すること
"""
