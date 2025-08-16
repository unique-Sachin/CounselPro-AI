from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import create_tables
from routes.counselor_route import router as counselor_router
from routes.session_route import router as session_router
from routes.video_analysis_route import router as video_analysis_router
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(counselor_router)
app.include_router(session_router)
app.include_router(video_analysis_router)


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "AI-Powered Counselor Excellence System"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
