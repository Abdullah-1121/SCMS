from datetime import datetime
from typing import List

from agents import RunContextWrapper
from scms.models.inventory import  InventoryItem, SupplyChainContext , metric


# Inventory management functions

def low_stock_items(inventory: List[InventoryItem] ):
    # In the Real Application , we will use a database query to fetch low stock items
    low_stock_items = [item for item in inventory if item.stock_level < item.reorder_threshold]
    return low_stock_items



def generate_metrics(ctx: RunContextWrapper[SupplyChainContext]) -> List[metric]:
    purchase_orders = ctx.context.purchase_orders
    restock_plan = ctx.context.restock_plan
    sla_violations = ctx.context.sla_violations
    low_stock_items = ctx.context.low_stock_items

    metrics = []

    # Total purchase orders
    metrics.append(metric(
        name="Total Purchase Orders",
        value=len(purchase_orders),
        unit="orders",
        description="Number of purchase orders generated"
    ))

    # SLA violations
    metrics.append(metric(
        name="SLA Violations",
        value=len(sla_violations),
        unit="violations",
        description="Number of SLA violations detected"
    ))

    # Average delivery lead time (in days)
    if restock_plan:
        total_days = 0
        for item in restock_plan:
            try:
                est_date = datetime.strptime(item.estimated_arrival, "%Y-%m-%d")
                order = next((po for po in purchase_orders if po.order_id == item.order_id), None)
                if order:
                    order_date = datetime.strptime(order.order_date, "%Y-%m-%d %H:%M:%S")
                    total_days += (est_date - order_date).days
            except Exception as e:
                continue
        avg_days = total_days / len(restock_plan) if restock_plan else 0
        metrics.append(metric(
            name="Average Delivery Lead Time",
            value=round(avg_days, 2),
            unit="days",
            description="Average estimated delivery duration for restock items"
        ))

    # Total low stock items
    metrics.append(metric(
        name="Low Stock Items",
        value=len(low_stock_items),
        unit="items",
        description="Number of items below reorder threshold"
    ))

    return metrics