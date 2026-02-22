from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

BASE_SQLALCHEMY_URL="sqlite:///./ABS.db"

engine=create_engine(BASE_SQLALCHEMY_URL,connect_args={"check_same_thread":False})

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()


def get_db():
  db=SessionLocal()
  try:
    yield db
  finally:
    db.close()