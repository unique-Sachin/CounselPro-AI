from fastapi import FastAPI, Request
import traceback
import logging
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import create_tables
from app.routes.counselor_route import router as counselor_router
from app.routes.session_route import router as session_router
from contextlib import asynccontextmanager
import uvicorn
import time

from app.exceptions.global_exception_handler import register_exception_handlers

# Configure logging
# logger = logging.getLogger("api_logger")
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

# Add console handler if not already added
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    for route in app.routes:
        print("🚀 Loaded route:", route.path, route.methods)
    yield


app = FastAPI(
    title="CounselPro AI - API - Version 1",
    description="AI-Powered Counselor Excellence System",
    version="1.0.0",
    lifespan=lifespan,
    debug=True,
)

# Register exception handlers FIRST
register_exception_handlers(app)

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


# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()
#     try:
#         response = await call_next(request)
#         process_time = (time.time() - start_time) * 1000
#         logger.info(
#             f"➡️ {request.method} {request.url.path} "
#             f"completed_in={process_time:.2f}ms "
#             f"status_code={response.status_code}"
#         )
#         return response
#     except Exception as e:
#         logger.error(
#             f"❌ Error while handling {request.method} {request.url.path}: "
#             f"{str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}"
#         )
#         raise


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response


app.include_router(counselor_router)
app.include_router(session_router)


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "AI-Powered Counselor Excellence System"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="127.0.0.1", port=8000, reload=True, log_level="debug"
    )
