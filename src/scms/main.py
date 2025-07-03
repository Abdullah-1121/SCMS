import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from scms.agent import agents_streaming, run_supply_chain , data
from scms.models.inventory import SupplyChainContext

app = FastAPI(
    title="Supply Chain Management System",
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

@app.get("/run-full-stream")
async def run_full_stream(request: Request):
    """
    Endpoint to run the supply chain management process and stream the audit trail.
    """
    async def stream():
        async for line in agents_streaming():
            if await request.is_disconnected():
                break
            yield line

    return StreamingResponse(stream(), media_type="text/event-stream")

uvicorn.run(app, host="0.0.0.0", port=8000)