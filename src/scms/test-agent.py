import datetime
from scms.DB.methods import inventory_update
from scms.models.inventory import InventoryItem


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

inventory_update(data)