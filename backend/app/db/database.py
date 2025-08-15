from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get the full DATABASE_URL from env
DATABASE_URL = os.getenv("DATABASE_URL")

# Create async engine
engine = create_async_engine(
    DATABASE_URL, echo=True, future=True  # Shows SQL queries in console
)

# Create session maker
AsyncSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for database models
Base = declarative_base()


# Database dependency
async def get_async_db():
    async with AsyncSession() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


# Create database tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Optional test function
if __name__ == "__main__":
    import asyncio
    from sqlalchemy import text

    async def test():
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version();"))
            print(result.all())

    asyncio.run(test())
