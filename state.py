"""State schema for the customer support graph."""
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import add_messages


class CustomerSupportState(TypedDict):
    """Shared state for the customer support graph."""
    # Conversation messages (LangChain message objects)
    messages: Annotated[list, add_messages]
    # Customer profile loaded at session start
    customer_info: dict
    # Location context (departure station, city, etc.)
    location_context: dict
    # Active bookings summary string for context
    active_bookings: str
    # Which agent handled the last message
    current_agent: str
    # Router classification result
    route: str
