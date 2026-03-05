from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import os

# BASE_SQLALCHEMY_URL="sqlite:///./ABS.db"
# BASE_SQLALCHEMY_URL="postgresql://postgres:pramodabsproject@db.ievjzmcdyztzxleaqzpq.supabase.co:5432/postgres"
# BASE_SQLALCHEMY_URL="postgresql://postgres.ievjzmcdyztzxleaqzpq:pramodabsproject@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
# BASE_SQLALCHEMY_URL="postgresql://abs_user:pramodabsproject@localhost:5432/abs_database"
# BASE_SQLALCHEMY_URL="postgresql://abs_user:pramodabsproject@abs_db:5432/abs_database"
BASE_SQLALCHEMY_URL=os.getenv("DATABASE_URL","sqlite:///./ABS.db")


# engine=create_engine(BASE_SQLALCHEMY_URL,connect_args={"check_same_thread":False})
engine=create_engine(BASE_SQLALCHEMY_URL)

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()


def get_db():
  db=SessionLocal()
  try:
    yield db
  finally:
    db.close()