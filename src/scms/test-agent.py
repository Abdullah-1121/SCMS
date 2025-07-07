import datetime
import os
import random
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
from scms.tools.tools import generate_metrics, low_stock_items
from scms.models.inventory import InventoryAgentOutput, RestockPlanItem , SupplyChainContext , InventoryItem , PurchaseOrder , SlaViolation
import uuid
from scms.DB.methods import fetch_inventory_items_as_pydantic
# Load environment variables from .env file
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

# Check if the API key is present; if not, raise an error
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")
if not langsmith_api_key:
    raise ValueError("LANGSMITH_API_KEY is not set. Please ensure it is defined in your .env file.")

# Set up tracing with LangSmith
set_trace_processors([OpenAIAgentsTracingProcessor()])

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

Inventory_Analyzer_instructions = f'''# Role and Objectives:
You are an **Inventory Management Agent** responsible for managing inventory in a supply chain management system.

Your main goal is to **Get the Inventory Data** `get_inventory_data` and then **Identify low stock items** using the provided tool.
Do not attempt to calculate or guess manually.
Always use the provided tools to perform the analysis.

# Tool Usage:
You have access to a tool called **`get_low_stock_items`**.
- This tool must be used to fetch inventory items that are **below the reorder threshold**.
- The tool accepts a list of `InventoryItem` objects, available in the context as `inventory_data`.

> 🔧 **Always call the tool** `get_low_stock_items` to get the low stock items.

# Instructions:

1. **Fetch Inventory Data**
   - Call the tool `get_inventory_data` to fetch the inventory data.
   - Do **not** try to infer this manually — always use the tool.
   - You will get a list of `InventoryItem` objects in the response.


2. **Get Low Stock Items**
   - Call the tool `get_low_stock_items(inventory_data)` to retrieve items that need restocking.
   - Pass the Data you get from the tool `get_inventory_data` to the tool `get_low_stock_items`.

3. **Respond With Output Format**
    Generate a well-written, human-readable statement summarizing the results.
     This will be used for the `audit_trail`.

📌 Example for audit trail:
- "Inventory analysis complete. The following items are below the reorder threshold: [...]"
- Or: "Inventory analysis complete. No items are below the reorder threshold."



# IMPORTANT:
- Do **not** try to infer the inventory data or low stock items manually.
- Do **not** perform reasoning to determine low stock.
- Do **not** skip tool calls even if the data seems obvious.
- You **must** always use the `get_inventory_data` and `get_low_stock_items` tool before generating the final output.
- ❗ No matter what, always call the tool `get_inventory_data` before `get_low_stock_items`. Never answer without using it.
- ✅ Provide a clear output summary suitable for the audit trail.
 '''

@function_tool(description_override="Get the inventory data",)
def get_inventory_data()->List[InventoryItem]:
    '''
    Fetches the inventory data from the database and returns it as a list of InventoryItem objects.
    Returns:
        A list of InventoryItem objects
    '''
    print('[DEBUG] Fetching inventory data...')
    items = fetch_inventory_items_as_pydantic()
    print(items)
    return items


@function_tool(description_override="Get low stock items from the inventory ",)
def get_low_stock_items(data : List[InventoryItem])->InventoryAgentOutput:
    '''
    Analyzes the inventory data to identify items that are below the reorder threshold.

    Args : 
        data (List[InventoryItem]): The inventory data as a list of InventoryItem objects.

    Returns: 
        - A list of InventoryItem objects that are below the reorder threshold if any otherwise none.
    '''
    print('[DEBUG] Analyzing inventory data for low stock items...' , data)
    inventory_data = low_stock_items(data)
    # print('[DEBUG] Low stock items:', inventory_data)
    # print(inventory_data)
    if not inventory_data:
        print("No low stock items found.")
        return InventoryAgentOutput(low_stock_items=[], is_reorder_required=False)
    else :
        print(inventory_data)
        return InventoryAgentOutput(low_stock_items=inventory_data, is_reorder_required=True)

class CustomHooks(AgentHooks):
    async def on_start(self, context: RunContextWrapper[None], agent: Agent):
        print(f"--------------------------------Starting agent: {agent.name}------------------------------------ ")
        pass
    async def on_tool_start(self, context:  RunContextWrapper[None], agent: Agent, tool: Tool):
        print(f"--------------------------------Starting tool: {tool.name}------------------------------------ ")
        pass
    async def on_tool_end(self, context:  RunContextWrapper[None], agent: Agent, tool: Tool, result: str):
        print(f"--------------------------------Ending tool: {tool.name}------------------------------------ ")
        pass

    async def on_end(self, context:  RunContextWrapper[None], agent: Agent, output: Any):
        print(f"--------------------------------Ending agent: {agent.name}------------------------------------ ")
        pass
agent_hooks = CustomHooks()
Inventory_Analyzer = Agent(
    name = "Inventory Analyzer",
    instructions=Inventory_Analyzer_instructions,
    tools=[get_inventory_data, get_low_stock_items],
    model = model,
    model_settings=ModelSettings(
        temperature = 0.3,
    ),
    hooks=agent_hooks,
    
)

async def run_agent():
    result = await Runner.run(
        starting_agent=Inventory_Analyzer,
        input=f'Analyze the inventory data and determine if any items need to be reordered. first use the get_inventory_data tool to get the inventory data and then use the get_low_stock_items tool to get the low stock items',
    )
    print(result.final_output)

asyncio.run(run_agent())
