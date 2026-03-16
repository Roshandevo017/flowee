"""
Database configuration - PostgreSQL via Supabase
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# PostgreSQL connection string
# Format: postgresql://user:password@host:port/dbname
# For Supabase: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:your_password@db.your-project.supabase.co:5432/postgres"
)

# For local development with Docker:
# DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/poomart"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False  # Set True for SQL debug logs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency - provides DB session per request, auto-closes after"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
