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
        print(f"------------------------------ {agent.name} has completed tool: {tool.name}")

    async def on_end(self, context: RunContextWrapper[SupplyChainContext], agent: Agent[SupplyChainContext], output: Any):
        print(f"-------------------------------{agent.name} has completed with output----------------------------")
        context.context.audit_trail.append(f" {agent.name} : {output}")
        if(agent.name == "SLA Agent"):
            # Generate and store metrics
           metrics = generate_metrics(context)
           context.context.metrics = metrics

           # Optionally log audit trail summary
           audit_str = "\n".join([f"{m.name}: {m.value} {m.unit} — {m.description}" for m in metrics])
           context.context.audit_trail.append(f"📊 Metrics Summary:\n{audit_str}")




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

> 🔧 **Always call the tool** `get_low_stock_items` to get the low stock items.

# Instructions:

1. **Perform Inventory Analysis**
   - Parse the `inventory_data` from the context.
   - Call the tool `get_low_stock_items(inventory_data)` to retrieve items that need restocking.
   - Never try to infer this manually — always use the tool.

2. **Respond With Output Format**
   - Return a structured response of type `InventoryAgentOutput`.
   - Include the list of low stock items under `low_stock_items`.
   - If the list is not empty, set `is_reorder_required` to `true`; otherwise, set it to `false`.
   - Additionally, generate a well-written, human-readable statement summarizing the results.
     This will be used for the `audit_trail`.

📌 Example for audit trail:
- "Inventory analysis complete. The following items are below the reorder threshold: [...]"
- Or: "Inventory analysis complete. No items are below the reorder threshold."

# Context:
You will receive a list called `inventory_data` containing:
- `item_id`, `name`, `stock_level`, `reorder_threshold`, `supplier`, `last_updated`.

Here is the current inventory:
{inventory_data}

This data **must be passed directly** to the tool `get_low_stock_items`.

# IMPORTANT:
- Do **not** perform reasoning to determine low stock.
- Do **not** skip tool calls even if the data seems obvious.
- You **must** always use the `get_low_stock_items` tool before generating the final output.
- ❗ No matter what, always call the tool `get_low_stock_items`. Never answer without using it.
- ✅ Provide a clear output summary suitable for the audit trail.


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
- Additionally, provide a **well-formatted summary statement** of the generated purchase orders (or state that none were created) that can be logged in the `audit_trail`.

📌 Example for audit trail:
- "Here are the generated purchase orders for the low stock items: [...]"
- Or: "No purchase orders were created because there were no low stock items."

# Context:
You have access to `low_stock_items`, a list of items that are below their reorder threshold.
Each item includes:
- item_id, name, stock_level, reorder_threshold, supplier, last_updated.

Here is the list of low stock items:
{ctx.context.low_stock_items}

# Important:
- Do not attempt to generate orders manually.
- Always rely on `generate_purchase_orders`.
- If no low stock items are found, clearly state that no purchase orders were created.
- Always include a clear output summary suitable for user-facing audit logs.

"""

def logistics_agent_instructions(ctx: RunContextWrapper[SupplyChainContext], agent):
    return f"""
# Role:
You are a Logistics Agent responsible for planning the delivery of items that have been ordered from suppliers in the supply chain system.

# Your Tasks:
1. Review the `purchase_orders` provided in the context.
2. For each order:
    - Select a logistics partner from this list: **FedEx, DHL, UPS**.
    - Choose a delivery method: **standard** or **express**.
    - Set an estimated arrival date (based on delivery method: e.g., express = 3 days, standard = 7 days).
3. Generate a list of `RestockPlanItem` objects containing complete delivery plans for each order.

# Tool Access:
Use the tool **`plan_logistics`** to complete your task.
> Do NOT guess or create plans manually — always use the tool provided.

# Output Format:
You must return:
- A structured list of `RestockPlanItem` objects for the context.
- A **clear and readable summary string** for the user, describing the logistics plan. This will be used in the **audit trail**.
  - Example format:  
    "Restock plan created: Order PO-123456 will be shipped by DHL via express delivery and is expected to arrive by 2025-07-03."

# Context Provided:
You have access to a list called `purchase_orders`, which includes:
- `order_id`, `item_id`, `supplier`, `order_date`, `item_name`, and `quantity`.

# Important:
- The logistics plan must be realistic and based on delivery rules (3–7 days).
- Ensure the output is both **machine-readable (RestockPlanItem)** and **human-readable (audit summary)**.
"""
def sla_instructions(ctx: RunContextWrapper[SupplyChainContext] , agent):
    return f"""
# SLA Monitoring Agent Instructions

## Role:
You are the SLA Monitoring Agent in a supply chain automation system. Your job is to monitor restock deliveries and ensure they meet the promised delivery dates (SLAs).

## Objective:
Identify if any restock plan item is delivered later than the `estimated_arrival` date.

## Tool Access:
You MUST use the tool `check_sla_violations` to verify SLA compliance.

## Workflow:
1. Access the `restock_plan` from the context.
2. Call the tool `check_sla_violations` to get all SLA violations.
3. If violations are found:
   - Add them to `sla_violations` in the context.
   - Generate a clear and helpful message to be added to the `audit_trail`.
   - Include order ID, supplier, and reason for delay.
4. If no violations are found:
   - Add a message to `audit_trail` stating that all deliveries are within SLA.

## Output:
- A summary message explaining the SLA results in simple language.
- This message will be logged in the audit trail for end-users.
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
def plan_logistics(ctx: RunContextWrapper[SupplyChainContext]):
    """
    Plan logistics for each purchase order using context data.
    """

    purchase_orders = ctx.context.purchase_orders
    logistics_partners = ["FedEx", "DHL", "UPS"]
    methods = ["standard", "express"]

    restock_plan = []

    for order in purchase_orders:
        partner = random.choice(logistics_partners)
        method = random.choice(methods)
        days = 3 if method == "express" else 7
        eta = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")

        restock_plan.append(RestockPlanItem(
            order_id=order.order_id,
            item_id=order.item_id,
            supplier=order.supplier,
            logistics_partner=partner,
            estimated_arrival=eta,
            delivery_method=method,
        ))

    # Store in context
    ctx.context.restock_plan = restock_plan
    return restock_plan

@function_tool(description_override="Check if any deliveries in restock plan are violating SLA deadlines")
def check_sla_violations(ctx: RunContextWrapper[SupplyChainContext]) -> List[SlaViolation]:
    today = datetime.datetime.now().date()
    violations = []

    for plan in ctx.context.restock_plan:
        try:
            expected = datetime.datetime.strptime(plan.estimated_arrival, "%Y-%m-%d").date()
            if today > expected:
                violation = SlaViolation(
                    order_id=plan.order_id,
                    supplier=plan.supplier,
                    reason=f"Late delivery: expected by {plan.estimated_arrival}",
                    reported_on=today.strftime("%Y-%m-%d")
                )
                violations.append(violation)
        except Exception as e:
            print(f"[ERROR] Date parsing failed for order {plan.order_id}: {e}")

    # Update context with violations
    ctx.context.sla_violations = violations
    return violations
# ==========================================     AGENTS DEFINITION  ============================================

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

logistics_agent = Agent[SupplyChainContext](
    name="Logistics Agent",
    instructions=logistics_agent_instructions,
    tools=[plan_logistics],
    model_settings=ModelSettings(
        temperature=0.3,
    ),
    hooks=run_hooks,
)

sla_agent = Agent[SupplyChainContext](
    name="SLA Agent",
    instructions=sla_instructions,
    tools=[check_sla_violations],
    model_settings=ModelSettings(
        temperature=0.3,
    ),
    hooks=run_hooks,
)

async def run_agent():
    data=[
    InventoryItem(
        item_id="A101",
        name="Laptop - Dell XPS 13",
        stock_level=1,
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
        stock_level=1,
        reorder_threshold=5,
        supplier="Samsung",
        last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    ),
    InventoryItem(
        item_id="D980",
        name="USB-C Docking Station - Anker",
        stock_level=1,
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
        print(f"----------------------------------Planning logistics for purchase-----------------------------------")
        

        logistics_plan = await Runner.run(
           starting_agent=logistics_agent,
           input=f'Plan logistics for the following purchase orders present in the context using the tools plan_logistics. ',
           context=run_context,
        run_config=config
    )
        print(f"----------------------------------Logistics plan generated---------------------------------------")
        print(logistics_plan.final_output)
        print(f"----------------------------------SLA Monitoring---------------------------------------")
        sla_violations = await Runner.run(
            starting_agent=sla_agent,
            input=f'Check if any deliveries in the restock plan are violating SLA deadlines using the tools check_sla_violations. ',
            context=run_context,
            run_config=config
        )
        print(f"----------------------------------SLA Violations---------------------------------------")
        print(sla_violations.final_output)

    print(f"----------------------------------Audit Trail---------------------------------------")
    # print(f"User ID: {run_context.user_id}")
    # print(f"Session ID: {run_context.session_id}")
    # print(f"Inventory Data: {run_context.inventory_data}")
    # print(f"Low Stock Items: {run_context.low_stock_items}")
    # print(f"Purchase Orders: {run_context.purchase_orders}")
    # print(f"Logistics Plan: {run_context.restock_plan}")
    # print(f"SLA Violations: {run_context.sla_violations}")
    for entry in enumerate(run_context.audit_trail, start=1):
        print(f'Agent Output {entry[0]}:', entry[1])


if __name__ == "__main__":
    
    asyncio.run(run_agent())