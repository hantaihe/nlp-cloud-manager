import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+aiomysql://{os.getenv('DATABASE_USERNAME', 'root')}:{os.getenv('DATABASE_PASSWORD', 'root')}@{os.getenv('DATABASE_HOST', '127.0.0.1')}:{os.getenv('DATABASE_PORT', '3306')}/{os.getenv('DATABASE_DATABASE', 'nlp_cloud_manager')}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
