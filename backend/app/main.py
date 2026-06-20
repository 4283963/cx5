from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import scan, intercept
from app.db.database import engine, Base
from app.db.init_db import init_database

settings = get_settings()

Base.metadata.create_all(bind=engine)
init_database()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="智慧物流分拨中心快递面单无损扫描与智能拦截系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix=settings.API_V1_STR, tags=["扫描识别"])
app.include_router(intercept.router, prefix=settings.API_V1_STR, tags=["拦截控制"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
