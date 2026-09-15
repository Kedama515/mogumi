"""ログインユーザーを作成/パスワードを更新する。

公開の登録エンドポイントは用意していない(個人利用のみ想定のため)。
ユーザー追加・パスワード変更はこのスクリプトから行う。

新規ユーザーには専用のhousehold(世帯)を自動作成して紐付ける。既存の
householdに参加させたい場合(家族で共有したい場合)は、まだ専用の招待
フローがないため、DBを直接操作するか別途スクリプトを用意すること。

実行方法(backend/ ディレクトリから):

    python3 -m scripts.create_user
"""

import getpass
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.security import hash_password  # noqa: E402


def main() -> None:
    username = input("username: ").strip()
    if not username:
        print("username is required")
        return
    password = getpass.getpass("password: ")
    if not password:
        print("password is required")
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            user.password_hash = hash_password(password)
            print(f"updated password for existing user: {username}")
        else:
            household = models.Household(name=f"{username}の世帯")
            db.add(household)
            db.flush()  # household.id を確定させる
            db.add(
                models.User(
                    username=username,
                    password_hash=hash_password(password),
                    household_id=household.id,
                )
            )
            print(f"created user: {username} (household: {household.name})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
