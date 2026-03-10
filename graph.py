"""Customer support StateGraph definition."""
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import CustomerSupportState
from nodes.router import router_node
from nodes.policy_agent import policy_agent_node
from nodes.ticket_agent import ticket_agent_node
from nodes.response import general_response_node


def route_by_intent(state: CustomerSupportState) -> Literal["policy_agent", "ticket_agent", "general_response"]:
    """Route to the appropriate agent based on classification."""
    route = state.get("route", "general")
    if route == "policy":
        return "policy_agent"
    elif route == "ticket":
        return "ticket_agent"
    else:
        return "general_response"


def build_graph(checkpointer=None):
    """Build and compile the customer support graph."""
    workflow = StateGraph(CustomerSupportState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("policy_agent", policy_agent_node)
    workflow.add_node("ticket_agent", ticket_agent_node)
    workflow.add_node("general_response", general_response_node)

    # Wire edges
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router",
        route_by_intent,
        ["policy_agent", "ticket_agent", "general_response"],
    )
    workflow.add_edge("policy_agent", END)
    workflow.add_edge("ticket_agent", END)
    workflow.add_edge("general_response", END)

    # Compile with optional checkpointer for session persistence
    if checkpointer is None:
        checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer)
