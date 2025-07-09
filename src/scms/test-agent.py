import datetime
from typing import List
import uuid
from scms.DB.methods import fetch_inventory_items_as_pydantic, insert_purchase_orders, inventory_update
from scms.models.inventory import InventoryItem, PurchaseOrder


data=[
    InventoryItem(
        item_id="A101",
        name="Laptop - Dell XPS 13",
        stock_level=12,
        reorder_threshold=10,
        supplier="Dell",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="B205",
        name="Mechanical Keyboard - Logitech",
        stock_level=5,
        reorder_threshold=20,
        supplier="Logitech",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="C332",
        name="27-inch Monitor - Samsung",
        stock_level=10,
        reorder_threshold=12,
        supplier="Samsung",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="D980",
        name="USB-C Docking Station - Anker",
        stock_level=12,
        reorder_threshold=10,
        supplier="Anker",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ),
    InventoryItem(
        item_id="E558",
        name="External Hard Drive - Seagate 2TB",
        stock_level=7,
        reorder_threshold=8,
        supplier="Seagate",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    )
]

# inventory_update(data)
def get_inventory_data()->List[InventoryItem]:
    '''
    Fetches the inventory data from the database and returns it as a list of InventoryItem objects.
    Returns:
        A list of InventoryItem objects
    '''
    print('\n \n[DEBUG] Fetching inventory data...')
    items = fetch_inventory_items_as_pydantic()
    print(items)
    return items

# get_inventory_data()
    
def generate_purchase_orders():
    """
    Generates purchase orders for all low stock items in the context.
    
    Args:
        ctx (RunContextWrapper[SupplyChainContext]): The shared supply chain context.

    Returns:
        List[PurchaseOrder]: A list of generated purchase orders.
    """

    # In a Real Application , we will get the suppliers from the database and then we will generate the purchase orders and then send them to the suppliers
    
    low_stock_items = [ InventoryItem(
        item_id="C332",
        name="27-inch Monitor - Samsung",
        stock_level=10,
        reorder_threshold=12,
        supplier="Samsung",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="D980",
        name="USB-C Docking Station - Anker",
        stock_level=12,
        reorder_threshold=10,
        supplier="Anker",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ),
    InventoryItem(
        item_id="E558",
        name="External Hard Drive - Seagate 2TB",
        stock_level=7,
        reorder_threshold=8,
        supplier="Seagate",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    )
]
    purchase_orders = []
    if not low_stock_items:
        return f"[WARN] No low stock items in context. Skipping PO generation."
    for item in low_stock_items:
        quantity_needed =  item.reorder_threshold

        order = PurchaseOrder(
            order_id=f"PO-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            item_id=item.item_id,
            item_name=item.name,
            quantity=quantity_needed,
            supplier=item.supplier,
            status="pending",
            order_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        purchase_orders.append(order)
    db_orders = [po.model_dump() for po in purchase_orders]
    insert_purchase_orders(db_orders, 'test_session_id')
    
    return purchase_orders

generate_purchase_orders()
    