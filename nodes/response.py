"""General response node — handles greetings and simple messages."""
from langchain_core.messages import SystemMessage

from config.model_config import get_chat_model
from state import CustomerSupportState


def general_response_node(state: CustomerSupportState) -> dict:
    """Generate a general response for greetings/simple messages."""
    model = get_chat_model(temperature=0.7)
    customer_name = state["customer_info"].get("name", "Customer")

    system_msg = SystemMessage(content=(
        f"You are a friendly customer support assistant for UKConnect Rail. "
        f"The customer's name is {customer_name}. "
        f"Respond warmly to greetings, thanks, and casual conversation. "
        f"If they seem to have a question, let them know you can help with "
        f"policies, bookings, refunds, and train information."
    ))

    response = model.invoke([system_msg] + state["messages"])
    return {"messages": [response]}
