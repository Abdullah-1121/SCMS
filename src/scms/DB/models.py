from sqlalchemy import JSON, Column, String, Integer, Float, DateTime, Text
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from scms.DB.db import Base


# class InventoryItem(Base):
#     __tablename__ = "inventory_items"

#     item_id = Column(String, primary_key=True, index=True)
#     name = Column(String)
#     stock_level = Column(Integer)
#     reorder_threshold = Column(Integer)
#     supplier = Column(String)
#     last_updated = Column(String)


# class Supplier(Base):
#     __tablename__ = "suppliers"

#     supplier_id = Column(String, primary_key=True, index=True)
#     name = Column(String)
#     contact_info = Column(Text)
#     rating = Column(Float)
#     last_order_date = Column(String)


# class Metric(Base):
#     __tablename__ = "metrics"

#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     name = Column(String)
#     value = Column(Float)
#     unit = Column(String)
#     description = Column(Text)
#     created_at = Column(DateTime, default=datetime.utcnow)


# class PurchaseOrder(Base):
#     __tablename__ = "purchase_orders"

#     order_id = Column(String, primary_key=True, index=True)
#     item_id = Column(String)
#     quantity = Column(Integer)
#     supplier = Column(String)
#     order_date = Column(String)
#     status = Column(String)
#     item_name = Column(String)


# class RestockPlanItem(Base):
#     __tablename__ = "restock_plan"

#     order_id = Column(String, primary_key=True, index=True)
#     item_id = Column(String)
#     supplier = Column(String)
#     logistics_partner = Column(String)
#     estimated_arrival = Column(String)
#     delivery_method = Column(String)


# class SlaViolation(Base):
#     __tablename__ = "sla_violations"

#     order_id = Column(String, primary_key=True, index=True)
#     supplier = Column(String)
#     reason = Column(String)
#     reported_on = Column(String)


class SupplyChainContextDB(Base):
    __tablename__ = "supply_chain_context"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    session_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    inventory_data = Column(JSON)  # Stores a list of inventory items
    low_stock_items = Column(JSON)

    restock_plan = Column(JSON)
    selected_suppliers = Column(JSON)
    purchase_orders = Column(JSON)

    metrics = Column(JSON)
    sla_violations = Column(JSON)

    audit_trail = Column(JSON)  # Stores event messages from audit trail