"""Model configuration for LangGraph agents."""
import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


def get_chat_model(temperature: float = 0.5, model_name: str | None = None) -> ChatGoogleGenerativeAI:
    """Get a configured Gemini chat model."""
    model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
    )


def get_router_model() -> ChatGoogleGenerativeAI:
    """Model for intent classification (low temperature for consistency)."""
    model_name = os.getenv("GEMINI_MODEL_ROUTER", None)
    return get_chat_model(temperature=0.1, model_name=model_name)


def get_policy_agent_model() -> ChatGoogleGenerativeAI:
    """Model for policy agent (moderate temperature)."""
    model_name = os.getenv("GEMINI_MODEL_POLICY", None)
    return get_chat_model(temperature=0.5, model_name=model_name)


def get_ticket_agent_model() -> ChatGoogleGenerativeAI:
    """Model for ticket agent (slightly creative)."""
    model_name = os.getenv("GEMINI_MODEL_TICKET", None)
    return get_chat_model(temperature=0.6, model_name=model_name)


def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Get the embeddings model for FAISS."""
    model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    return GoogleGenerativeAIEmbeddings(model=model)
