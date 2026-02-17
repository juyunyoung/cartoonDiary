import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# AWS RDS Configuration
DB_HOST = os.getenv("DB_HOST", "cartoondirary-instance-1.cq9e6aiu6jnt.us-east-1.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "cartoonadmin")
DB_PASS = os.getenv("DB_PASSWORD", "") # User must provide this
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# SSL Context for AWS RDS
ssl_context = ssl.create_default_context(cafile="certs/global-bundle.pem")
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Check if password is set to decide between RDS or SQLite fallback
if DB_PASS:
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    connect_args = {"ssl": ssl_context}
else:
    # Fallback to local SQLite if no password provided (Dev mode)
    print("Warning: DB_PASSWORD not set. Using local SQLite.")
    DATABASE_URL = "sqlite+aiosqlite:///./cdiary.db"
    connect_args = {}

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args=connect_args
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
