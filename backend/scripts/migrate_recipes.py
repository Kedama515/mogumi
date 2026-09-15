"""ai-project/menu/recipes/*.md をmogumiのrecipesテーブルに取り込む。

実行方法(backend/ ディレクトリから):

    python3 -m scripts.migrate_recipes [username]

username を省略した場合、DBにユーザーが1人だけならそのユーザーのhousehold宛に
取り込む。複数いる場合は指定が必須。

対象は「YAMLフロントマター(tags) + `# 料理名` + `## 材料`(- 箇条書き) +
`## 手順`(番号付きリスト) + 任意で `## メモ`・`出典: ...` 行」という
ai-project/menu/recipes/ の記法。それ以外の地の文(出典行、タイトル直後の
説明文、末尾の「初出: ...」など)はmemoにまとめて取り込む。

指定したhouseholdのrecipes/recipe_tagsを全削除してから取り込み直すため、
何度でも再実行可能。
"""

import json
import re
import sys
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from scripts._household import resolve_household_id  # noqa: E402

MENU_RECIPES_DIR = BACKEND_DIR.parent.parent / "menu" / "recipes"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)
SOURCE_RE = re.compile(r"出典[:：]\s*(?:\[[^\]]*\]\((https?://[^)]+)\)|(https?://\S+))")
SECTION_RE = re.compile(r"^##\s*(.+)$", re.M)
TAG_CATEGORIES = ("protein", "cuisine", "cooking_method", "style")


def normalize_tag_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def parse_recipe_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"frontmatter not found: {path}")
    frontmatter_raw, body = m.groups()

    frontmatter = yaml.safe_load(frontmatter_raw) or {}
    raw_tags = frontmatter.get("tags") or {}
    tags = {category: normalize_tag_list(raw_tags.get(category)) for category in TAG_CATEGORIES}

    title_match = TITLE_RE.search(body)
    dish_name = title_match.group(1).strip() if title_match else path.stem
    body_after_title = body[title_match.end() :] if title_match else body

    source_match = SOURCE_RE.search(body_after_title)
    source_url = (source_match.group(1) or source_match.group(2)) if source_match else ""

    headers = list(SECTION_RE.finditer(body_after_title))
    preamble = body_after_title[: headers[0].start()] if headers else body_after_title
    sections: list[tuple[str, str]] = []
    for i, h in enumerate(headers):
        name = h.group(1).strip()
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body_after_title)
        sections.append((name, body_after_title[start:end]))

    ingredients: list[str] = []
    steps: list[str] = []
    memo_lines: list[str] = [
        line.strip()
        for line in preamble.splitlines()
        if line.strip() and not line.strip().startswith("出典")
    ]

    for name, content in sections:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if name.startswith("材料"):
            for line in lines:
                if line.startswith("- "):
                    ingredients.append(line[2:].strip())
                else:
                    memo_lines.append(line)
        elif name.startswith("手順"):
            for line in lines:
                step_match = re.match(r"^\d+\.\s*(.+)$", line)
                if step_match:
                    steps.append(step_match.group(1).strip())
                else:
                    memo_lines.append(line)
        elif name.startswith("メモ"):
            for line in lines:
                memo_lines.append(line[2:].strip() if line.startswith("- ") else line)
        else:
            memo_lines.extend(lines)

    return {
        "dish_name": dish_name,
        "source_url": source_url or "",
        "ingredients": ingredients,
        "steps": steps,
        "memo": "\n".join(memo_lines),
        "tags": tags,
    }


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        username = sys.argv[1] if len(sys.argv) > 1 else None
        household_id = resolve_household_id(db, username)

        db.query(models.RecipeTag).filter(
            models.RecipeTag.recipe_id.in_(
                db.query(models.Recipe.id).filter(models.Recipe.household_id == household_id)
            )
        ).delete(synchronize_session=False)
        db.query(models.Recipe).filter(models.Recipe.household_id == household_id).delete()
        db.commit()

        count = 0
        for path in sorted(MENU_RECIPES_DIR.glob("*.md")):
            data = parse_recipe_file(path)
            db_recipe = models.Recipe(
                household_id=household_id,
                dish_name=data["dish_name"],
                source_url=data["source_url"],
                ingredients=json.dumps(data["ingredients"], ensure_ascii=False),
                steps=json.dumps(data["steps"], ensure_ascii=False),
                memo=data["memo"],
            )
            for category, values in data["tags"].items():
                for value in values:
                    db_recipe.tags.append(models.RecipeTag(category=category, value=value))
            db.add(db_recipe)
            count += 1
            print(f"imported: {data['dish_name']} ({path.name})")
        db.commit()
        print(f"recipes: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
