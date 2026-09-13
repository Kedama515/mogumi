from . import schemas


def tags_to_schema(tag_rows) -> schemas.Tags:
    grouped: dict[str, list[str]] = {"protein": [], "cuisine": [], "cooking_method": [], "style": []}
    for tag in tag_rows:
        grouped.setdefault(tag.category, []).append(tag.value)
    return schemas.Tags(**grouped)
