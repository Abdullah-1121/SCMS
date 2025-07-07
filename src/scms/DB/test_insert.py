import datetime
from scms.DB.db import get_session  # your session setup
from scms.DB.models import InventoryData, SupplyChainContext
from sqlmodel import Session
import json

context_dict = {
  "user_id": "123",
  "session_id": "abc-123",
  "inventory_data": [
    {
      "item_id": "A101",
      "name": "Laptop - Dell XPS 13",
      "stock_level": 12,
      "reorder_threshold": 10,
      "supplier": "Dell",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "B205",
      "name": "Mechanical Keyboard - Logitech",
      "stock_level": 5,
      "reorder_threshold": 20,
      "supplier": "Logitech",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "C332",
      "name": "27-inch Monitor - Samsung",
      "stock_level": 10,
      "reorder_threshold": 12,
      "supplier": "Samsung",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "D980",
      "name": "USB-C Docking Station - Anker",
      "stock_level": 12,
      "reorder_threshold": 10,
      "supplier": "Anker",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "E558",
      "name": "External Hard Drive - Seagate 2TB",
      "stock_level": 7,
      "reorder_threshold": 8,
      "supplier": "Seagate",
      "last_updated": "2025-07-07 10:30:05"
    }
  ],
  "low_stock_items": [
    {
      "item_id": "B205",
      "name": "Mechanical Keyboard - Logitech",
      "stock_level": 5,
      "reorder_threshold": 20,
      "supplier": "Logitech",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "C332",
      "name": "27-inch Monitor - Samsung",
      "stock_level": 10,
      "reorder_threshold": 12,
      "supplier": "Samsung",
      "last_updated": "2025-07-07 10:30:05"
    },
    {
      "item_id": "E558",
      "name": "External Hard Drive - Seagate 2TB",
      "stock_level": 7,
      "reorder_threshold": 8,
      "supplier": "Seagate",
      "last_updated": "2025-07-07 10:30:05"
    }
  ],
  "restock_plan": [
    {
      "order_id": "PO-20250707-1DD353",
      "item_id": "B205",
      "supplier": "Logitech",
      "logistics_partner": "UPS",
      "estimated_arrival": "2025-07-10",
      "delivery_method": "express"
    },
    {
      "order_id": "PO-20250707-D9F9BF",
      "item_id": "C332",
      "supplier": "Samsung",
      "logistics_partner": "DHL",
      "estimated_arrival": "2025-07-10",
      "delivery_method": "express"
    },
    {
      "order_id": "PO-20250707-CCF4C2",
      "item_id": "E558",
      "supplier": "Seagate",
      "logistics_partner": "DHL",
      "estimated_arrival": "2025-07-10",
      "delivery_method": "express"
    }
  ],
  "selected_suppliers": [],
  "purchase_orders": [
    {
      "order_id": "PO-20250707-1DD353",
      "item_id": "B205",
      "quantity": 20,
      "supplier": "Logitech",
      "order_date": "2025-07-07 10:30:20",
      "status": "pending",
      "item_name": "Mechanical Keyboard - Logitech"
    },
    {
      "order_id": "PO-20250707-D9F9BF",
      "item_id": "C332",
      "quantity": 12,
      "supplier": "Samsung",
      "order_date": "2025-07-07 10:30:20",
      "status": "pending",
      "item_name": "27-inch Monitor - Samsung"
    },
    {
      "order_id": "PO-20250707-CCF4C2",
      "item_id": "E558",
      "quantity": 8,
      "supplier": "Seagate",
      "order_date": "2025-07-07 10:30:20",
      "status": "pending",
      "item_name": "External Hard Drive - Seagate 2TB"
    }
  ],
  "metrics": [],
  "sla_violations": [],
  "audit_trail": [
    " Inventory Analyzer Agent : low_stock_items=[InventoryItem(item_id='B205', name='Mechanical Keyboard - Logitech', stock_level=5, reorder_threshold=20, supplier='Logitech', last_updated='2025-07-07 10:30:05'), InventoryItem(item_id='C332', name='27-inch Monitor - Samsung', stock_level=10, reorder_threshold=12, supplier='Samsung', last_updated='2025-07-07 10:30:05'), InventoryItem(item_id='E558', name='External Hard Drive - Seagate 2TB', stock_level=7, reorder_threshold=8, supplier='Seagate', last_updated='2025-07-07 10:30:05')] is_reorder_required=True",
    " Procurement Agent : Here are the generated purchase orders for the low stock items: ['PurchaseOrder(order_id='PO-20250707-1DD353', item_id='B205', quantity=20, supplier='Logitech', order_date='2025-07-07 10:30:20', status='pending', item_name='Mechanical Keyboard - Logitech'), PurchaseOrder(order_id='PO-20250707-D9F9BF', item_id='C332', quantity=12, supplier='Samsung', order_date='2025-07-07 10:30:20', status='pending', item_name='27-inch Monitor - Samsung'), PurchaseOrder(order_id='PO-20250707-CCF4C2', item_id='E558', quantity=8, supplier='Seagate', order_date='2025-07-07 10:30:20', status='pending', item_name='External Hard Drive - Seagate 2TB')]\n",
    " Logistics Agent : Restock plan created: Order PO-20250707-1DD353 will be shipped by UPS via express delivery and is expected to arrive by 2025-07-10. Order PO-20250707-D9F9BF will be shipped by DHL via express delivery and is expected to arrive by 2025-07-10. Order PO-20250707-CCF4C2 will be shipped by DHL via express delivery and is expected to arrive by 2025-07-10.\n"
  ]
}
def insert_context(data: dict):
    context = SupplyChainContext(
        user_id=data["user_id"],
        session_id=data["session_id"],
        timestamp=datetime.datetime.now(),
        inventory_data=json.dumps(data["inventory_data"]),
        low_stock_items=json.dumps(data["low_stock_items"]),
        restock_plan=json.dumps(data["restock_plan"]),
        selected_suppliers=json.dumps(data["selected_suppliers"]),
        purchase_orders=json.dumps(data["purchase_orders"]),
        metrics=json.dumps(data["metrics"]),
        sla_violations=json.dumps(data["sla_violations"]),
        audit_trail=json.dumps(data["audit_trail"])
    )

    with get_session() as session:
        session.add(context)
        session.commit()
        print("✅ SupplyChainContext inserted")

insert_context(data = context_dict)


