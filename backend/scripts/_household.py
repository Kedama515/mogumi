"""移行スクリプト共通: 対象householdの解決。"""

from app import models


def resolve_household_id(db, username: str | None) -> int:
    if username:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise SystemExit(f"user not found: {username}")
        return user.household_id

    users = db.query(models.User).all()
    if len(users) == 1:
        return users[0].household_id
    if len(users) == 0:
        raise SystemExit(
            "ユーザーが存在しません。先に python3 -m scripts.create_user を実行してください。"
        )
    usernames = ", ".join(u.username for u in users)
    raise SystemExit(f"ユーザーが複数存在するため username の指定が必要です: {usernames}")
