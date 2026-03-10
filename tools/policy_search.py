"""Policy search tool using FAISS vector store."""
from langchain_core.tools import tool

from database.vector_store import get_vector_store

_vector_store = None


def _get_vs():
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store


@tool
def search_policy_knowledge(query: str, k: int = 5) -> str:
    """Search the UKConnect policy knowledge base for information about company policies,
    refund rules, cancellation procedures, booking terms, payment policies, and FAQs.

    Args:
        query: The search query about policies or procedures
        k: Number of results to return (default 5)
    """
    vs = _get_vs()
    results = vs.similarity_search_with_score(query, k=k)

    if not results:
        return "No relevant policy information found."

    output_parts = []
    for i, (doc, score) in enumerate(results, 1):
        relevance = round(1 - score / 2, 3)  # Convert distance to similarity
        section = doc.metadata.get("section", "General")
        topics = doc.metadata.get("topics", "")
        output_parts.append(
            f"Result {i} (Relevance: {relevance}):\n"
            f"Section: {section}\n"
            f"{doc.page_content}\n"
            f"Topics: {topics}\n"
        )

    return "\n---\n".join(output_parts)
