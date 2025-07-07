from scms.DB.db import SessionLocal
from scms.DB.models import SupplyChainContextDB
from datetime import datetime

def insert_sample_context():
    db = SessionLocal()

    try:
        context = SupplyChainContextDB(
            user_id="user_123",
            session_id="session_abc_456",
            timestamp=datetime.utcnow(),
            inventory_data=[{
                "item_id": "item001",
                "name": "Widget A",
                "stock_level": 10,
                "reorder_threshold": 20,
                "supplier": "Supplier X",
                "last_updated": "2025-07-03"
            }],
            low_stock_items=[],
            restock_plan=[],
            selected_suppliers=[],
            purchase_orders=[],
            metrics=[],
            sla_violations=[],
            audit_trail=["Started analysis", "Completed"]
        )

        db.add(context)
        db.commit()
        print("✅ Sample context inserted successfully.")

    except Exception as e:
        print(f"❌ Error inserting sample: {e}")
        db.rollback()
    finally:
        db.close()

insert_sample_context()
