
# Production AI Customer Support — LangGraph Edition

[![GitHub stars](https://img.shields.io/github/stars/ntg2208/production-ai-customer-support-langchain?style=social)](https://github.com/ntg2208/production-ai-customer-support-langchain/stargazers)
[![GitHub sponsors](https://img.shields.io/github/sponsors/ntg2208)](https://github.com/sponsors/ntg2208)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://coff.ee/truonggiang2208)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20me-ff5e5b)](https://ko-fi.com/S6S71IXKGS)

> **The same enterprise-grade AI customer support system — rebuilt with LangGraph, LangChain & FAISS**

🤖 **Original Google ADK version: [production-ai-customer-support](https://github.com/ntg2208/production-ai-customer-support)**

🎥 **[Watch the Tutorial Series →](https://www.youtube.com/@truonggiangai)**

## ✨ What's Different in This Version

This is a **LangGraph rewrite** of the original Google ADK customer support agent. Same functionality, different framework:

| Feature | ADK Version | LangGraph Version |
|---------|------------|-------------------|
| Agent Framework | Google ADK (`LlmAgent`) | LangGraph (`StateGraph` + `create_react_agent`) |
| Routing | ADK implicit delegation | Explicit conditional edges |
| Vector DB | Custom sklearn cosine similarity | FAISS via LangChain |
| LLM Provider | Google Gemini (ADK) | Google Gemini (`ChatGoogleGenerativeAI`) |
| State Management | ADK session state | LangGraph `MemorySaver` checkpointer |
| Dependencies | `google-adk` | `langchain`, `langgraph`, `langchain-google-genai` |

## 🏗️ Architecture

```
User Input (terminal)
        │
   StateGraph
        │
  Router Node (LLM classifies: policy / ticket / general)
        │
        ├── policy ──► Policy Agent Node (ReAct + FAISS RAG)
        ├── ticket ──► Ticket Agent Node (ReAct + 13 SQLite tools)
        └── general ─► General Response Node
        │
  Response → END
```

**State flows through the graph:**
```python
CustomerSupportState:
  messages        # conversation history (add_messages reducer)
  customer_info   # loaded customer profile
  location_context # departure station, city
  active_bookings  # summary for ticket agent context
  route            # router classification result
```

## ✨ Key Features

- 🤖 **LangGraph StateGraph** — explicit routing with conditional edges
- 🧠 **FAISS RAG** — semantic policy search with `GoogleGenerativeAIEmbeddings`
- 🌍 **Location Intelligence** — smart departure station detection from customer address
- 🗄️ **13 SQLite Tools** — search, book, refund, check availability
- 💬 **Multi-turn Conversations** — `MemorySaver` checkpointer persists state per session
- 🧭 **Intent Router** — low-temperature Gemini call classifies every message
- 🐍 **Python 3.10+** — modern type annotations throughout

## 🚀 Quick Start (30 seconds)

```bash
git clone https://github.com/ntg2208/production-ai-customer-support-langchain
cd production-ai-customer-support-langchain
```

```bash
# Install dependencies (uv recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

```bash
# Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

```bash
# Initialize database with sample data
uv run python -c "from utils.create_schema import create_database_schema; create_database_schema()"
uv run python -c "from utils.populate_data import populate_data; populate_data()"
```

```bash
# Run the terminal chat
uv run python main.py
```

## 💬 Terminal Chat Demo

```
=== UKConnect Customer Support (LangGraph) ===

Select a customer profile:
  1. James Thompson (james.thompson@email.co.uk)
  2. Sarah Williams (sarah.williams@email.co.uk)
  ...

Customer: James Thompson
Default Station: London Euston

You: Hello!
[general agent]
Assistant: Hello James! Welcome to UKConnect Rail. How can I help you today?

You: What's your refund policy for flexible tickets?
[policy agent]
Assistant: For Flexible Fares, UKConnect offers a full refund without any fees...

You: Show me tickets to Manchester tomorrow
[ticket agent]
Assistant: Here's what I found for tomorrow:
  Ticket ID: 101 | London Euston → Manchester Piccadilly | 11:30 | £89 | Flexible
  Ticket ID: 102 | London Euston → Manchester Piccadilly | 14:00 | £65 | Standard
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini 2.5 Flash |
| Agent Framework | LangGraph `StateGraph` + `create_react_agent` |
| LLM Provider | `langchain-google-genai` (`ChatGoogleGenerativeAI`) |
| Embeddings | `GoogleGenerativeAIEmbeddings` (`gemini-embedding-001`) |
| Vector Store | FAISS (`langchain-community`) |
| Database | SQLite via `UKConnectDB` (40+ methods) |
| Checkpointer | LangGraph `MemorySaver` |
| Python | 3.10+ |

## 📁 Project Structure

```
production-ai-customer-support-langchain/
├── main.py                  # Terminal chat entry point
├── graph.py                 # StateGraph definition
├── state.py                 # CustomerSupportState schema
├── nodes/
│   ├── router.py            # Intent classification node
│   ├── policy_agent.py      # RAG-powered policy specialist
│   ├── ticket_agent.py      # Booking operations specialist
│   └── response.py          # General response handler
├── tools/
│   ├── policy_search.py     # FAISS search @tool
│   └── ticket_tools.py      # 13 SQLite booking @tools
├── prompts/
│   ├── router.py            # Router classification prompt
│   ├── policy_agent.py      # Sarah (policy specialist) prompt
│   └── ticket_agent.py      # Mark (booking specialist) prompt
├── database/
│   ├── database.py          # UKConnectDB (40+ methods)
│   ├── vector_store.py      # FAISS build/load
│   ├── UKConnect_policy.txt # Policy knowledge base
│   └── ukconnect_rag_chunks.json # 129 Q&A chunks
├── config/
│   ├── model_config.py      # ChatGoogleGenerativeAI setup
│   └── time_config.py       # Configurable system time
└── utils/
    ├── location_intelligence.py  # Address → station mapping
    ├── city_station_mapping.py   # 50+ UK cities/stations
    ├── create_schema.py          # DB schema creation
    └── populate_data.py          # Sample data (10 customers)
```

## 🧩 How the Routing Works

Every user message goes through the **router node** first:

```python
# Router classifies into: "policy" | "ticket" | "general"
route = model.invoke([
    SystemMessage(content=ROUTER_SYSTEM_PROMPT.format(...)),
    HumanMessage(content=user_message),
])

# Conditional edges dispatch to the right agent
graph.add_conditional_edges("router", route_by_intent, [
    "policy_agent", "ticket_agent", "general_response"
])
```

**Policy queries** → `create_react_agent` with `search_policy_knowledge` (FAISS)

**Ticket queries** → `create_react_agent` with 13 tools:
- `search_available_tickets`, `search_tickets_from_city`, `search_tickets_to_city`
- `search_tickets_by_city`, `search_routes_between_cities`
- `book_ticket`, `get_customer_bookings`, `get_active_tickets_for_customer`
- `refund_ticket`, `calculate_refund_amount`, `get_available_ticket_details`
- `check_seat_availability`, `get_location_suggestions`

## 🌍 Location Intelligence

The system auto-detects each customer's default departure station from their address:

```python
# Customer in Bloomsbury, London → London Euston
# Customer in Manchester → Manchester Piccadilly
# Customer near Edinburgh → Edinburgh Waverley

location_context = get_customer_location_context(customer_info)
# → {"default_departure_station": "London Euston", "location_city": "London", ...}
```

When a customer says "show me tickets to Manchester", the ticket agent automatically uses their detected station as the departure point — no asking needed.

## ⚙️ Configuration

### Environment Variables

```bash
GOOGLE_API_KEY=your-key-here          # Required

# Optional: override models
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODEL_ROUTER=gemini-2.5-flash
GEMINI_MODEL_POLICY=gemini-2.5-flash
GEMINI_MODEL_TICKET=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

# Optional: LangSmith tracing
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=ukconnect-langchain
```

### Time Configuration

Control system time for reproducible testing:

```python
# config/time_config.py
SYSTEM_CURRENT_TIME = "2025-07-29 14:30:00"  # Fixed time for testing
# SYSTEM_CURRENT_TIME = None                  # Use real current time
```

### Rebuild FAISS Index

If you update `ukconnect_rag_chunks.json`, delete `database/faiss_index/` and restart — it rebuilds automatically.

## 🗺️ Roadmap

- [ ] **Guardrails** — Input/output filtering nodes (PII detection, prompt injection defense)
- [ ] **Evaluation Framework** — Port the 15 test scenarios from the ADK version
- [ ] **Gradio Web UI** — Chat interface with agent flow visualization
- [ ] **LangSmith Evaluation** — Automated scoring with routing accuracy metrics
- [ ] **Store-based Memory** — Cross-session customer preference memory

## 🔗 Related

- **[Original ADK Version](https://github.com/ntg2208/production-ai-customer-support)** — Google ADK implementation with guardrails, evaluation, and Gradio UI
- **[Tutorial Series](https://www.youtube.com/@truonggiangai)** — Step-by-step build walkthrough

## 💰 Support This Project

If this helps you or your company:

- ⭐ **Star this repository** (free, helps others find it)
- 💖 **[Sponsor on GitHub](https://github.com/sponsors/ntg2208)** (monthly support)
- ☕ **[Buy me a coffee](https://coff.ee/truonggiang2208)** (one-time donation)
- 🎯 **[Support on Ko-fi](https://ko-fi.com/S6S71IXKGS)** (one-time or monthly)
- 💼 **[Hire for consulting](https://twentytwotensors.co.uk)** (custom implementations)

## 🏢 Enterprise Support

Need this customised for your business?

**[Get Enterprise Implementation →](https://twentytwotensors.co.uk/contact)**
- Custom domain adaptation (healthcare, e-commerce, hospitality)
- Integration with existing CRM/ERP systems
- Production deployment support
- Training and ongoing maintenance

## 🤝 Contributing

Contributions welcome! Areas we need help:
- 🛡️ **Guardrails** — Port the ADK guardrail callbacks to LangGraph nodes
- 📊 **Evaluation** — LangSmith-based eval suite for the 15 test scenarios
- 🌐 **Translations** — Multi-language support
- 🏭 **Industry Adaptations** — Healthcare, e-commerce examples
- 📚 **Documentation** — Tutorials, guides

## 📄 License

MIT License — see [LICENSE](LICENSE) file

## 👨‍💻 About the Creator

Built by **[Truong Giang Nguyen](https://twentytwotensors.co.uk)** — ML Engineer specialising in production AI systems.

- 🌐 Website: [twentytwotensors.co.uk](https://twentytwotensors.co.uk)
- 📺 YouTube: [@truonggiangai](https://www.youtube.com/@truonggiangai)
- 💼 LinkedIn: [linkedin.com/in/ntg2208](https://linkedin.com/in/ntg2208)
- 📧 Email: ntg2208@gmail.com

---

⭐ **Star this repo if it helps you build better AI agents with LangGraph!**
