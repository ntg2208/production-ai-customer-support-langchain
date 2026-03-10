"""Policy agent node — RAG-powered policy specialist."""
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from config.model_config import get_policy_agent_model
from prompts.policy_agent import POLICY_AGENT_SYSTEM_PROMPT
from tools.policy_search import search_policy_knowledge
from state import CustomerSupportState


def policy_agent_node(state: CustomerSupportState) -> dict:
    """Run the policy agent on the current conversation."""
    model = get_policy_agent_model()
    system_prompt = POLICY_AGENT_SYSTEM_PROMPT.format(
        customer_name=state["customer_info"].get("name", "Customer"),
        customer_id=state["customer_info"].get("customer_id", ""),
    )
    agent = create_react_agent(
        model=model,
        tools=[search_policy_knowledge],
        prompt=system_prompt,
    )
    input_count = len(state["messages"])
    result = agent.invoke({"messages": state["messages"]})
    # Extract only new messages
    new_messages = result["messages"][input_count:]
    # Return only the final AI response
    ai_messages = [m for m in new_messages if isinstance(m, AIMessage) and m.content]
    return {"messages": ai_messages[-1:] if ai_messages else new_messages[-1:]}
