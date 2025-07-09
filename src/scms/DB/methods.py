from typing import List
from scms.DB.db import get_session
from scms.DB.models import InventoryDataDB, LowStockItemDB , PurchaseOrderDB, RestockPlanItemDB , SlaViolationsDB
from scms.models.inventory import InventoryItem, RestockPlanItem , SlaViolation , PurchaseOrder

def fetch_inventory_items_as_pydantic():
    with get_session() as session:
        db_items = session.query(InventoryDataDB).all()
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
def get_purchase_orders():
    with get_session() as session:
        db_items = session.query(PurchaseOrderDB).all()
        pydantic_items = [
            PurchaseOrder(
                order_id=item.order_id,
                item_id=item.item_id,
                quantity=item.quantity,
                supplier=item.supplier,
                order_date=item.order_date,
                status=item.status,
                item_name=item.item_name
            )
            for item in db_items
        ]
        return pydantic_items

def get_restock_plan():
    with get_session() as session:
        db_items = session.query(RestockPlanItemDB).all()
        pydantic_items = [
            RestockPlanItem(
                order_id=item.order_id,
                item_id=item.item_id,
                supplier=item.supplier,
                logistics_partner=item.logistics_partner,
                estimated_arrival=item.estimated_arrival,
                delivery_method=item.delivery_method
            )
            for item in db_items
        ]
        return pydantic_items
            
def inventory_update(items: List[InventoryItem]):
    with get_session() as session:
        to_insert = []
        for item in items:
            if not session.query(InventoryDataDB).filter_by(item_id=item.item_id).first():
                to_insert.append(
                    InventoryDataDB(
                        item_id=item.item_id,
                        name=item.name,
                        stock_level=item.stock_level,
                        reorder_threshold=item.reorder_threshold,
                        supplier=item.supplier,
                        last_updated=item.last_updated
                    )
                )
        if to_insert:
            session.add_all(to_insert)
            session.commit()

def insert_purchase_orders(purchase_order_list: list[dict], session_id: str):
    with get_session() as session:
        for order in purchase_order_list:
            session.add(PurchaseOrderDB(**order, session_id=session_id))
        session.commit()

def insert_restock_plan(restock_plan_list: list[dict], session_id: str):
    with get_session() as session:
        for order in restock_plan_list:
            session.add(RestockPlanItemDB(**order, session_id=session_id))
        session.commit()

def insert_sla_violations(sla_violations_list: list[dict], session_id: str):
    with get_session() as session:
        for order in sla_violations_list:        
            session.add(SlaViolationsDB(**order, session_id=session_id))
        session.commit()

def insert_low_stock_items(items: List[InventoryItem]):
    with get_session() as session:
        for item in items:
            exists = session.query(LowStockItemDB).filter_by(item_id=item.item_id).first()
            if not exists:
                new_entry = LowStockItemDB(
                    item_id=item.item_id,
                    name=item.name,
                    stock_level=item.stock_level,
                    reorder_threshold=item.reorder_threshold,
                    supplier=item.supplier,
                    last_updated=item.last_updated
                )
                session.add(new_entry)
        session.commit()
def filter_new_low_stock_items(new_items: List[InventoryItem]) -> List[InventoryItem]:
    with get_session() as session:
        existing_ids = {item.item_id for item in session.query(LowStockItemDB.item_id).all()}
        unique_items = [item for item in new_items if item.item_id not in existing_ids]
        return unique_items        

def get_low_stock_items():
    with get_session() as session:
        db_items = session.query(LowStockItemDB).all()
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
    
def get_sla_violations():
    with get_session() as session:
        db_items = session.query(SlaViolationsDB).all()
        pydantic_items = [
            SlaViolation(
                item_id=item.item_id,
                name=item.name,
                stock_level=item.stock_level,
                reorder_threshold=item.reorder_threshold,
                supplier=item.supplier,
                last_updated=item.last_updated
            )
            for item in db_items
        ]    