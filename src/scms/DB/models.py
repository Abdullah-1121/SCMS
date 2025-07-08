from typing import Optional
import uuid
from datetime import datetime
from sqlmodel import SQLModel , Field



class SupplyChainContextDB(SQLModel, table=True):
    id:int | None = Field(default=None,primary_key=True)
    user_id: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    inventory_data: str  # JSON serialized list of InventoryItem
    low_stock_items: str  # JSON list of InventoryItem
    restock_plan: str     # JSON list of RestockPlanItem
    selected_suppliers: str  # JSON list of Supplier
    purchase_orders: str  # JSON list of PurchaseOrder
    metrics: str  # JSON list of Metric
    sla_violations: str  # JSON list of SlaViolation
    audit_trail: str  # JSON list of string messages


class InventoryDataDB(SQLModel, table=True):
    id:int | None = Field(default=None,primary_key=True)
    item_id: str
    name: str
    stock_level: int
    reorder_threshold: int
    supplier: str
    last_updated: str

class PurchaseOrderDB(SQLModel, table=True):
    id:int | None = Field(default=None,primary_key=True)
    order_id: str
    item_id: str
    quantity: int
    supplier: str
    order_date: str
    status: str
    item_name: str
       

class RestockPlanItemDB(SQLModel, table=True):
    id:int | None = Field(default=None,primary_key=True)
    order_id: str
    item_id: str
    supplier: str
    logistics_partner: str
    estimated_arrival: str
    delivery_method: str       

class SlaViolationsDB(SQLModel, table=True):
    id:int | None = Field(default=None,primary_key=True)
    order_id: str
    supplier: str
    reason: str
    reported_on: str

class LowStockItemDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_id: str = Field(index=True)
    name: str
    stock_level: int
    reorder_threshold: int
    supplier: str
    last_updated: str  # ISO timestamp string        