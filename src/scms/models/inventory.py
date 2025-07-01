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
    name: str
    value: float
    unit: str
    description: str

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

class PurchaseOrder(BaseModel):
    order_id: str = Field(... , description="Unique identifier for the purchase order")
    item_id: str = Field(... , description="Identifier for the item being ordered")
    quantity: int = Field(... , description="Quantity of the item to be ordered")
    supplier: str = Field(... , description="Supplier of the item")
    order_date: str = Field(... , description="Date when the order was placed")
    status: str = Field(... , description="Current status of the order")
    item_name: str = Field(... , description="Name of the item being ordered")

class RestockPlanItem(BaseModel):
    order_id: str = Field(... , description="Unique identifier for the restock order")
    item_id: str = Field(... , description="Identifier for the item being restocked")
    supplier: str = Field(... , description="Supplier of the item")
    logistics_partner: str = Field(... , description="Logistics partner handling the delivery")
    estimated_arrival: str = Field(... , description="Estimated arrival date of the restock")
    delivery_method: str = Field(... , description="Delivery method for the restock")

class SlaViolation(BaseModel):
    order_id: str  = Field(... , description="Unique identifier for the order associated with the SLA violation")                   
    supplier: str  = Field(... , description="Supplier responsible for the delay")                       
    reason: str  = Field(... , description="Reason for violation (e.g., 'Late delivery')")                        
    reported_on: str  = Field(... , description="Date when the violation was reported")     