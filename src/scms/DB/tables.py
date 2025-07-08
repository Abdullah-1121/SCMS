from sqlmodel import SQLModel
from scms.DB.db import engine 
from scms.DB.models import SupplyChainContextDB , InventoryDataDB
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


create_db_and_tables()