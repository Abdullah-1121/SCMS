from scms.DB.db import get_session
from scms.DB.models import InventoryData , PurchaseOrder, RestockPlanItem , SlaViolations
from scms.models.inventory import InventoryItem , SlaViolation , PurchaseOrder

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
def get_purchase_orders():
    with get_session() as session:
        db_items = session.query(PurchaseOrder).all()
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
        db_items = session.query(RestockPlanItem).all()
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
            
         
def insert_purchase_orders(purchase_order_list: list[dict], session_id: str):
    with get_session() as session:
        for order in purchase_order_list:
            session.add(PurchaseOrder(**order, session_id=session_id))
        session.commit()

def insert_restock_plan(restock_plan_list: list[dict], session_id: str):
    with get_session() as session:
        for order in restock_plan_list:
            session.add(RestockPlanItem(**order, session_id=session_id))
        session.commit()

def insert_sla_violations(sla_violations_list: list[dict], session_id: str):
    with get_session() as session:
        for order in sla_violations_list:        
            session.add(SlaViolations(**order, session_id=session_id))
        session.commit()
        