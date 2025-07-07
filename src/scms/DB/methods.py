from scms.DB.db import get_session
from scms.DB.models import InventoryData
from scms.models.inventory import InventoryItem

def fetch_inventory_items_as_pydantic():
    with get_session() as session:
        db_items = session.query(InventoryData).all()
        pydantic_items = [
            InventoryItem(
                item_id=item.item_id,
                name=item.name,
                stock_level=item.stock_level,
                reorder_threshold=item.reorder_threshold,
                supplier=item.supplier,
                last_updated=item.last_updated
            )
            for item in db_items
        ]
        return pydantic_items

items = fetch_inventory_items_as_pydantic()
print(items)