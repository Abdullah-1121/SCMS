from datetime import datetime
from typing import List
from scms.models.inventory import dummy_inventory , InventoryItem


# Inventory management functions

def low_stock_items(inventory: List[InventoryItem] ):
    # In the Real Application , we will use a database query to fetch low stock items
    low_stock_items = [item for item in inventory if item.stock_level < item.reorder_threshold]
    return low_stock_items

# def generate_purchase_order(items:List[InventoryItem] ):
#     # In the Real Application , we will use a database query to generate purchase order
#     purchase_orders = []
#     for item in items:
#         purchase_order = {
#             "order_id": f"PO-{item.item_id}",
#             "item_id": item.item_id,
#             "quantity": item.stock_level,
#             "supplier": item.supplier,
#             "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
#             "status": "Pending"
#         }
#         purchase_orders.append(purchase_order)
#     return purchase_orders
