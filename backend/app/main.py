from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from .database import Base, engine  # noqa: E402
from .routers import fridge, meals, pantry, suggestions  # noqa: E402

Base.metadata.create_all(bind=engine)

app = FastAPI(title="mogumi API")

app.include_router(fridge.router, prefix="/api/fridge", tags=["fridge"])
app.include_router(pantry.router, prefix="/api/pantry", tags=["pantry"])
app.include_router(meals.router, prefix="/api/meals", tags=["meals"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["suggestions"])


@app.get("/health")
def health():
    return {"status": "ok"}
