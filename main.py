"""Terminal chat interface for UKConnect customer support."""
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

from graph import build_graph
from database.database import UKConnectDB
from utils.location_intelligence import get_customer_location_context

# Customer profiles
CUSTOMER_PROFILES = {
    "1": "james.thompson@email.co.uk",
    "2": "sarah.williams@email.co.uk",
    "3": "michael.davies@email.co.uk",
    "4": "emily.johnson@email.co.uk",
    "5": "robert.brown@email.co.uk",
    "6": "lisa.wilson@email.co.uk",
    "7": "david.evans@email.co.uk",
    "8": "jennifer.smith@email.co.uk",
    "9": "christopher.jones@email.co.uk",
    "10": "amanda.taylor@email.co.uk",
}


def load_customer(email: str) -> dict:
    """Load customer data and location context from the database."""
    db = UKConnectDB()
    customer = db.find_customer_by_email(email)
    if not customer:
        print(f"Customer not found: {email}")
        sys.exit(1)

    customer_info = dict(customer)
    location_context = get_customer_location_context(customer_info)

    bookings = db.get_customer_bookings(customer_info["customer_id"])
    active_bookings = "None"
    if bookings:
        booking_strs = []
        for b in list(bookings)[:5]:
            booking_strs.append(
                f"  - {b['booking_reference']}: {b['from_station']} → {b['to_station']} "
                f"on {b['departure_time']} ({b['travel_status']})"
            )
        active_bookings = "\n".join(booking_strs)

    return {
        "customer_info": customer_info,
        "location_context": location_context,
        "active_bookings": active_bookings,
    }


def select_customer() -> dict:
    """Let user pick a customer profile."""
    print("\n=== UKConnect Customer Support (LangGraph) ===\n")

    # Show available profiles by loading names from DB
    db = UKConnectDB()
    print("Select a customer profile:")
    for key, email in CUSTOMER_PROFILES.items():
        customer = db.find_customer_by_email(email)
        name = customer["name"] if customer else email
        print(f"  {key}. {name} ({email})")
    print()

    choice = input("Enter number (1-10) [default: 1]: ").strip() or "1"
    if choice not in CUSTOMER_PROFILES:
        print("Invalid choice, using default (1)")
        choice = "1"

    email = CUSTOMER_PROFILES[choice]
    print(f"\nLoading profile for {email}...")
    return load_customer(email)


def main():
    """Run the terminal chat loop."""
    customer_data = select_customer()
    graph = build_graph()

    customer_name = customer_data["customer_info"].get("name", "Customer")
    station = customer_data["location_context"].get("default_departure_station", "Unknown")
    print(f"\nCustomer: {customer_name}")
    print(f"Default Station: {station}")
    print("\nType 'quit' to exit, 'switch' to change customer.\n")

    thread_id = f"session-{customer_data['customer_info'].get('customer_id', '1')}"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if user_input.lower() == "switch":
            customer_data = select_customer()
            thread_id = f"session-{customer_data['customer_info'].get('customer_id', '1')}"
            config = {"configurable": {"thread_id": thread_id}}
            continue

        input_state = {
            "messages": [HumanMessage(content=user_input)],
            "customer_info": customer_data["customer_info"],
            "location_context": customer_data["location_context"],
            "active_bookings": customer_data["active_bookings"],
            "current_agent": "",
            "route": "",
        }

        try:
            result = graph.invoke(input_state, config=config)
            route = result.get("route", "unknown")
            last_msg = result["messages"][-1]
            print(f"\n[{route} agent]")
            if hasattr(last_msg, "content") and last_msg.content:
                print(f"Assistant: {last_msg.content}\n")
            else:
                print("Assistant: [No response generated]\n")

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
