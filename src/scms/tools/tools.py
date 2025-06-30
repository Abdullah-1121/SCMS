from typing import List
from scms.models.inventory import dummy_inventory , InventoryItem


# Inventory management functions

def low_stock_items(inventory: List[InventoryItem] ):
    # In the Real Application , we will use a database query to fetch low stock items
    low_stock_items = [item for item in inventory if item.stock_level < item.reorder_threshold]
    return low_stock_items

# # Example usage
# low_stock_items =low_stock_items(dummy_inventory)
# for item in low_stock_items:
#     print(f"Low stock item: {item.name} (ID: {item.item_id}) - Stock Level: {item.stock_level}, Reorder Threshold: {item.reorder_threshold}")
