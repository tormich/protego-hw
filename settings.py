from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from os import environ
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_USER = environ.get("POSTGRES_USER")
DB_PASSWORD = environ.get("POSTGRES_PASSWORD")
DB_HOST = environ.get("POSTGRES_HOST")
DB_PORT = environ.get("POSTGRES_PORT")
DB_NAME = environ.get("POSTGRES_DB")

# Construct database URL
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
