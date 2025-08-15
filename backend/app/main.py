from fastapi import FastAPI
from db.database import create_tables
from routes.counselor_route import router as counselor_router
from routes.session_route import router as session_router
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="CounselPro AI - API - Version 1",
    description="AI-Powered Counselor Excellence System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(counselor_router)
app.include_router(session_router)


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "AI-Powered Counselor Excellence System"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
