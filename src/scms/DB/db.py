from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker , declarative_base
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
connection_string : str = str(DATABASE_URL).replace("postgresql","postgresql+psycopg2")
engine = create_engine(connection_string, connect_args={"sslmode": "require"}  ,pool_recycle=300 )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
with engine.connect() as conn:
    result = conn.execute(text("SELECT Version()"))
    print(f'NEON DB Version: {result.scalar()}')
