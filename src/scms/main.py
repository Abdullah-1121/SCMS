import datetime
import os
from agents import ( Agent, AgentOutputSchema, FunctionToolResult, GuardrailFunctionOutput, InputGuardrailTripwireTriggered, ItemHelpers, ModelSettings, OutputGuardrailTripwireTriggered, RunHooks, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, TResponseInputItem, Tool, ToolsToFinalOutputResult , handoff,Handoff,function_tool , AgentOutputSchemaBase, input_guardrail, output_guardrail, set_trace_processors , RunContextWrapper , handoffs , HandoffInputData , HandoffInputFilter , AgentHooks )
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX , prompt_with_handoff_instructions
from agents.run import RunConfig
from dotenv import load_dotenv
import asyncio
from agents.tracing import set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent
from dataclasses import dataclass
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from typing import Any, List
from agents.extensions import handoff_filters
from pydantic import BaseModel
from scms.tools.tools import low_stock_items
from scms.models.inventory import InventoryAgentOutput , SupplyChainContext , InventoryItem , PurchaseOrder
from scms.instructions.instructions import inventory_agent_instructions
import uuid

# Load environment variables from .env file
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

# Check if the API key is present; if not, raise an error
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")
if not langsmith_api_key:
    raise ValueError("LANGSMITH_API_KEY is not set. Please ensure it is defined in your .env file.")
trace = set_trace_processors([OpenAIAgentsTracingProcessor()])

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True,
    workflow_name='' \
    'SCMS Inventory Management Agent',
)
class CustomHooks(AgentHooks):
    async def on_start(self, context: RunContextWrapper[SupplyChainContext], agent: Agent[SupplyChainContext]):
        print(f"--------------------------------Starting agent: {agent.name}------------------------------------ ")
    async def on_tool_start(self, context: RunContextWrapper[SupplyChainContext], agent: Agent[SupplyChainContext], tool: Tool):
        print(f"-------------------------------{agent.name} is starting tool: {tool.name}-----------------------")
    async def on_tool_end(self, context: RunContextWrapper[SupplyChainContext], agent: Agent[SupplyChainContext], tool: Tool, result: str):
        print(f"------------------------------ {agent.name} has completed tool: {tool.name}----------------------with result: {result}----------------------------")

    async def on_end(self, context: RunContextWrapper[SupplyChainContext], agent: Agent[SupplyChainContext], output: Any):
        print(f"-------------------------------{agent.name} has completed with output----------------------------")
        context.context.audit_trail.append(f" {agent.name} : {output}")



run_hooks = CustomHooks()       

def inventory_instructions(ctx:RunContextWrapper[SupplyChainContext], agent : Agent[SupplyChainContext]):

    inventory_data = ctx.context.inventory_data
    return f""" 
# Role and Objectives:
You are an **Inventory Management Agent** responsible for managing inventory in a supply chain management system.

Your main goal is to **identify low stock items** using the provided tool. Do not attempt to calculate or guess manually.

# Tool Usage:
You have access to a tool called **`get_low_stock_items`**.
- This tool must be used to fetch inventory items that are **below the reorder threshold**.
- The tool accepts a list of `InventoryItem` objects, available in the context as `inventory_data`.

> 🔧 **Always call the tool** `get_low_stock_items` to get the low stock items .

# Instructions:

1. **Perform Inventory Analysis**
   - Parse the `inventory_data` from the context.
   - Call the tool `get_low_stock_items(inventory_data)` to retrieve items that need restocking.
   - Never try to infer this manually — always use the tool.

2. **Respond With Output Format**
   - Return a structured response of type `InventoryAgentOutput`.
   - Include the list of low stock items under `low_stock_items`.
   - If the list is not empty, set `is_reorder_required` to `true`; otherwise, set it to `false`.

# Context:
You will receive a list called `inventory_data` containing:
- `item_id`, `name`, `stock_level`, `reorder_threshold`, `supplier`, `last_updated`.
 {inventory_data}

This data **must be passed directly** to the tool `get_low_stock_items`.

# IMPORTANT:
- Do **not** perform reasoning to determine low stock.
- Do **not** skip tool calls even if the data seems obvious.
- You **must** always use the `get_low_stock_items` tool before generating the final output.
- No Matter Always call the tool `get_low_stock_items` and dont try to answer without calling the tool.

"""
def procurement_instructions(ctx:RunContextWrapper[SupplyChainContext], agent : Agent[SupplyChainContext]):
    return f"""
# Role and Objective:
You are a **Procurement Agent** in a Supply Chain Management System. Your primary responsibility is to ensure that all items flagged as low in stock are ordered from their respective suppliers.

# Your Responsibilities:
- Review the inventory analysis results available in the context.
- Identify `low_stock_items` in the context that require reordering.
- Generate purchase orders for these items using the tool provided.

# Tool Usage:
You MUST use the tool **`generate_purchase_orders`** to generate purchase orders.
- Do NOT manually calculate or fabricate orders.
- This tool takes the `low_stock_items` from the context and generates structured `PurchaseOrder` objects.
- Each `PurchaseOrder` contains order_id, item_name, quantity_to_order, supplier, status, and timestamp.

> ✅ Always call `generate_purchase_orders` to perform procurement.

# Output Format:
- Return the list of generated `PurchaseOrder` objects.
- Do not fabricate data or guess any fields.
- Only return what the tool generates.

# Context:
You have access to `low_stock_items`, a list of items that are below their reorder threshold.
Each item includes:
- item_id, name, stock_level, reorder_threshold, supplier, last_updated.
Here is the list of low stock items:
{ctx.context.low_stock_items}

# Important:
- Do not attempt to generate orders manually.
- Always rely on `generate_purchase_orders`.
- If no low stock items are found, confirm no purchase orders were created.

"""

@function_tool(description_override="Get low stock items from the inventory ",)
def get_low_stock_items(ctx:RunContextWrapper[SupplyChainContext]):
    '''
    Analyzes the inventory data to identify items that are below the reorder threshold.

    Args : 
        ctx (RunContextWrapper[SupplyChainContext]): The context containing the inventory data.

    Returns: 
        - A list of InventoryItem objects that are below the reorder threshold if any otherwise none.
    '''
    print('[DEBUG] Analyzing inventory data for low stock items...' , ctx.context.inventory_data)
    inventory_data = low_stock_items(ctx.context.inventory_data)
    # print('[DEBUG] Low stock items:', inventory_data)
    # print(inventory_data)
    if not inventory_data:
        print("No low stock items found.")
    else :
        ctx.context.low_stock_items = inventory_data
        return InventoryAgentOutput(low_stock_items=inventory_data, is_reorder_required=True)
        
@function_tool(description_override="Generate purchase orders for low stock items")
def generate_purchase_orders(ctx: RunContextWrapper[SupplyChainContext]):
    """
    Generates purchase orders for all low stock items in the context.
    
    Args:
        ctx (RunContextWrapper[SupplyChainContext]): The shared supply chain context.

    Returns:
        List[PurchaseOrder]: A list of generated purchase orders.
    """

    # In a Real Application , we will get the suppliers from the database and then we will generate the purchase orders and then send them to the suppliers
    
    low_stock_items = ctx.context.low_stock_items
    purchase_orders = []
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

    ctx.context.purchase_orders = purchase_orders
    return purchase_orders
    


@function_tool
def get_weather(city : str):
    '''
    Fetches the current weather for a given city.

    Args:
        city (str): The name of the city to get the weather for.

    Returns:
        str: A string containing the current weather information.
    '''
    return f"The current weather in {city} is sunny with a temperature of 25°C." 
inventory_analyzer_agent = Agent[SupplyChainContext](
    name = "Inventory Analyzer Agent",
    instructions = inventory_instructions,
    tools= [get_low_stock_items],
    model_settings=ModelSettings(
        temperature = 0.3,
    ),
    tool_use_behavior="stop_on_first_tool",
    # output_type=InventoryAgentOutput,
    hooks=run_hooks
)

procurement_agent = Agent[SupplyChainContext](
    name="Procurement Agent",
    instructions=procurement_instructions,
    tools=[generate_purchase_orders],
    model_settings=ModelSettings(
        temperature=0.3,
    ),
    hooks=run_hooks
)


async def run_agent():
    data=[
    InventoryItem(
        item_id="A101",
        name="Laptop - Dell XPS 13",
        stock_level=11,
        reorder_threshold=10,
        supplier="Dell",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="B205",
        name="Mechanical Keyboard - Logitech",
        stock_level=50,
        reorder_threshold=20,
        supplier="Logitech",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="C332",
        name="27-inch Monitor - Samsung",
        stock_level=7,
        reorder_threshold=5,
        supplier="Samsung",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="D980",
        name="USB-C Docking Station - Anker",
        stock_level=2,
        reorder_threshold=10,
        supplier="Anker",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ),
    InventoryItem(
        item_id="E558",
        name="External Hard Drive - Seagate 2TB",
        stock_level=11,
        reorder_threshold=8,
        supplier="Seagate",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    )
]
    run_context = SupplyChainContext(
        user_id="123",
        session_id="abc-123",
        inventory_data=data,
    )
    inventory_result = await Runner.run(
        starting_agent=inventory_analyzer_agent,
          input=f'Analyze the inventory data and determine if any items need to be reordered. use the get_low_stock_items tool to get the low stock items', context=run_context, run_config=config)
    print(f"=========================Inventory Analysis Result================================")
    print(inventory_result.final_output)
    if run_context.low_stock_items:
        print(f"----------------------------------Low stock items identified---------------------------------------")
        print(f"----------------------------------Generating purchase orders---------------------------------------")
        purchase_orders = await Runner.run(
            starting_agent=procurement_agent,
            input=f'Generate purchase orders for the following low stock items present in the context using the tools generate_purchase_orders. ',
            context=run_context,
            run_config=config
        )
        print(f"----------------------------------Purchase orders generated---------------------------------------")
        print(purchase_orders.final_output)
    print(run_context)    

    
    
if __name__ == "__main__":
    
    asyncio.run(run_agent())