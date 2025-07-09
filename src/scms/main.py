import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from scms.agent import agents_streaming, run_supply_chain , data
from scms.models.inventory import SupplyChainContext
from scms.DB.methods import get_low_stock_items , get_purchase_orders , get_sla_violations ,fetch_inventory_items_as_pydantic , get_restock_plan
app = FastAPI(
    title="AutoLogix",
    description="API for managing supply chain operations including inventory, purchase orders, and SLA violations.",
    version="1.0.0",
)
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Supply Chain Management System API"}
audit_stream = []
@app.get("/run" , response_model=SupplyChainContext)
async def run():
    """
    Endpoint to trigger the supply chain management process.
    This will run the main supply chain logic defined in scms.main.
    """
    data = await run_supply_chain()
    return data # run_context
@app.get("/inventory")
def inventory_data():
    return fetch_inventory_items_as_pydantic()

@app.get("/low-stock")
def low_stock_data():
    return get_low_stock_items()

@app.get("/purchase-orders")
def purchase_orders_data():
    return get_purchase_orders()

@app.get("/sla-violations")
def sla_violations_data():
    return get_sla_violations()
@app.get("/run-full-stream")
async def run_full_stream(request: Request):
    async def stream():
        try:
            async for line in agents_streaming():
                if await request.is_disconnected():
                    print("[INFO] Client disconnected")
                    break
                yield line
        except Exception as e:
            print(f"[STREAM ERROR] {e}")
            yield f"data: [ERROR] Streaming failed: {str(e)}\n\n"
        else:
            # ✅ Gracefully end stream
            yield "event: end\ndata: done\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

uvicorn.run(app, host="0.0.0.0", port=8000)