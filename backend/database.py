import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection string
# In Docker, the host should be 'postgres' (the service name in docker-compose)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:admin@postgres:5432/enterprise_kb"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
