import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection string
# In a real app, this should come from environment variables.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5432/enterprise_kb")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
