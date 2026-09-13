from dotenv import load_dotenv
from fastapi import Depends, FastAPI

load_dotenv()

from .database import Base, engine  # noqa: E402
from .routers import auth, fridge, meals, pantry, suggestions  # noqa: E402
from .security import get_current_user  # noqa: E402

Base.metadata.create_all(bind=engine)

app = FastAPI(title="mogumi API")

authed = [Depends(get_current_user)]

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(fridge.router, prefix="/api/fridge", tags=["fridge"], dependencies=authed)
app.include_router(pantry.router, prefix="/api/pantry", tags=["pantry"], dependencies=authed)
app.include_router(meals.router, prefix="/api/meals", tags=["meals"], dependencies=authed)
app.include_router(
    suggestions.router, prefix="/api/suggestions", tags=["suggestions"], dependencies=authed
)


@app.get("/health")
def health():
    return {"status": "ok"}
