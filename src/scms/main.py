from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from scms.agent import run_supply_chain
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

@app.get("/run" , response_model=SupplyChainContext)
async def run():
    """
    Endpoint to trigger the supply chain management process.
    This will run the main supply chain logic defined in scms.main.
    """
    data = await run_supply_chain()
    return data


uvicorn.run(app, host="0.0.0.0", port=8000)