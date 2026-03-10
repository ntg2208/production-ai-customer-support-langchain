"""Router node — classifies user intent."""
from langchain_core.messages import HumanMessage, SystemMessage

from config.model_config import get_router_model
from prompts.router import ROUTER_SYSTEM_PROMPT
from state import CustomerSupportState


def router_node(state: CustomerSupportState) -> dict:
    """Classify the latest user message and set the route."""
    model = get_router_model()

    system_msg = ROUTER_SYSTEM_PROMPT.format(
        customer_name=state["customer_info"].get("name", "Customer"),
        customer_id=state["customer_info"].get("customer_id", ""),
        customer_email=state["customer_info"].get("email", ""),
        default_departure_station=state["location_context"].get("default_departure_station", ""),
    )

    # Get last user message
    last_message = state["messages"][-1]

    response = model.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=last_message.content),
    ])

    route = response.content.strip().lower().strip('"')
    # Validate route
    if route not in ("policy", "ticket", "general"):
        route = "general"

    return {"route": route, "current_agent": route}
