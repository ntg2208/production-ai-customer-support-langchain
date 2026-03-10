"""FAISS vector store for policy document search."""
import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config.model_config import get_embeddings_model

DB_DIR = Path(__file__).parent
CHUNKS_PATH = DB_DIR / "ukconnect_rag_chunks.json"
FAISS_INDEX_DIR = DB_DIR / "faiss_index"


def load_chunks() -> list[Document]:
    """Load RAG chunks from JSON and convert to LangChain Documents."""
    with open(CHUNKS_PATH, "r") as f:
        chunks = json.load(f)

    documents = []
    for chunk in chunks:
        # The main text field contains "Question: ...\nAnswer: ..." already
        content = chunk.get("text", "")
        # Metadata (section, topics) lives under "metadata" key
        chunk_meta = chunk.get("metadata", {})
        metadata = {
            "section": chunk_meta.get("section", ""),
            "topics": ", ".join(chunk_meta.get("topics", [])),
            "chunk_id": chunk.get("id", ""),
        }
        documents.append(Document(page_content=content, metadata=metadata))

    return documents


def build_vector_store() -> FAISS:
    """Build FAISS index from chunks. Saves to disk for reuse."""
    embeddings = get_embeddings_model()
    documents = load_chunks()
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(str(FAISS_INDEX_DIR))
    return vector_store


def get_vector_store() -> FAISS:
    """Load existing FAISS index or build a new one."""
    embeddings = get_embeddings_model()
    if FAISS_INDEX_DIR.exists():
        # allow_dangerous_deserialization=True is required for FAISS pickle loading.
        # Safe here: the index is built from our own data and stored locally.
        return FAISS.load_local(
            str(FAISS_INDEX_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return build_vector_store()
