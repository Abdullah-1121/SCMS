from contextlib import contextmanager
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
connection_string : str = str(DATABASE_URL).replace("postgresql","postgresql+psycopg2")
engine = create_engine(connection_string, connect_args={"sslmode": "require"}  ,pool_recycle=300 )
def create_Tables():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

