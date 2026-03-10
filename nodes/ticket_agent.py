"""Ticket agent node — booking operations specialist."""
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from config.model_config import get_ticket_agent_model
from config.time_config import get_system_time_display
from prompts.ticket_agent import TICKET_AGENT_SYSTEM_PROMPT
from tools.ticket_tools import get_all_ticket_tools
from state import CustomerSupportState


def ticket_agent_node(state: CustomerSupportState) -> dict:
    """Run the ticket agent on the current conversation."""
    model = get_ticket_agent_model()
    system_prompt = TICKET_AGENT_SYSTEM_PROMPT.format(
        customer_name=state["customer_info"].get("name", "Customer"),
        customer_id=state["customer_info"].get("customer_id", ""),
        customer_email=state["customer_info"].get("email", ""),
        default_departure_station=state["location_context"].get("default_departure_station", ""),
        location_city=state["location_context"].get("location_city", ""),
        travel_context=state["location_context"].get("travel_context", ""),
        date_time=get_system_time_display(),
        active_bookings=state.get("active_bookings", "None"),
    )
    agent = create_react_agent(
        model=model,
        tools=get_all_ticket_tools(),
        prompt=system_prompt,
    )
    input_count = len(state["messages"])
    result = agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][input_count:]
    ai_messages = [m for m in new_messages if isinstance(m, AIMessage) and m.content]
    return {"messages": ai_messages[-1:] if ai_messages else new_messages[-1:]}
