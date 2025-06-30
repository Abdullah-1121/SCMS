from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

# Inventory item model
class InventoryItem(BaseModel):
    item_id: str
    name: str
    stock_level: int
    reorder_threshold: int
    supplier: str
    last_updated: str

# Dummy inventory data
dummy_inventory: List[InventoryItem] = [
    InventoryItem(
        item_id="A101",
        name="Laptop - Dell XPS 13",
        stock_level=8,
        reorder_threshold=10,
        supplier="Dell",
        last_updated='Todays date'
    ),
    InventoryItem(
        item_id="B205",
        name="Mechanical Keyboard - Logitech",
        stock_level=50,
        reorder_threshold=20,
        supplier="Logitech",
        last_updated='Todays date'
    ),
    InventoryItem(
        item_id="C332",
        name="27-inch Monitor - Samsung",
        stock_level=3,
        reorder_threshold=5,
        supplier="Samsung",
        last_updated='Todays date'
    ),
    InventoryItem(
        item_id="D980",
        name="USB-C Docking Station - Anker",
        stock_level=15,
        reorder_threshold=10,
        supplier="Anker",
        last_updated='Todays date'
    ),
    InventoryItem(
        item_id="E558",
        name="External Hard Drive - Seagate 2TB",
        stock_level=2,
        reorder_threshold=8,
        supplier="Seagate",
        last_updated='Todays date'
    )
]

class InventoryAgentOutput(BaseModel):
    low_stock_items: List[InventoryItem]
    is_reorder_required: bool

class suppliers(BaseModel):
    supplier_id: str
    name: str
    contact_info: str
    rating: float
    last_order_date: str

class metric(BaseModel):
    metric_id: str
    name: str
    value: float
    target_value: float
    last_updated: str

class SupplyChainContext(BaseModel):
    user_id: str
    session_id: str
    # timestamp: datetime = Field(default_factory=datetime.now())
    # Inventory Analysis
    inventory_data: List[InventoryItem] = Field(default_factory=list)
    low_stock_items: List[InventoryItem] = Field(default_factory=list)
    # Procurement Process
    restock_plan: List[str] = Field(default_factory=list)
    selected_suppliers: List[suppliers] = Field(default_factory=list)
    purchase_orders: List[str] = Field(default_factory=list)
    # Performance & SLA
    metrics: List[metric] = Field(default_factory=list)
    sla_violations: List[str] = Field(default_factory=list)
    # Status & Logs
    audit_trail: List[str] = Field(default_factory=list)
