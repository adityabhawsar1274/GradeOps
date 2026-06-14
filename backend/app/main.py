from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import seed_demo_users
from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import auth, exams, files, review


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(exams.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(files.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
