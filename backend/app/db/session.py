from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


