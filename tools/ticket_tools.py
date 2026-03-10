"""
Ticket Agent Tools
Direct copy from external agent_tools.py for ticket search, booking, and refund functionality.
"""

import sqlite3
from typing import Dict, Optional
from langchain_core.tools import tool

from database.database import UKConnectDB
from utils.city_station_mapping import get_stations_by_city, normalize_location_input, search_cities_and_stations
from config.time_config import get_system_time_iso

# Configuration - now uses centralized time
CURRENT_DATE = get_system_time_iso()  # Gets time from centralized config

# Database connection helper
def get_database_connection():
    """Create and return a new database connection using centralized time config"""
    db = UKConnectDB()  # Uses default database path and centralized time config
    if not db.connect():
        raise Exception("Failed to connect to enhanced database!")
    return db

# Validation functions
def validate_email(email: str) -> None:
    """Validate email format"""
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    if "@" not in email or "." not in email:
        raise ValueError("Invalid email format")

def validate_booking_reference(booking_ref: str) -> None:
    """Validate booking reference format"""
    if not booking_ref or not isinstance(booking_ref, str):
        raise ValueError("Booking reference must be a non-empty string")
    if len(booking_ref) < 3:
        raise ValueError("Booking reference too short")

def validate_station_name(station_name: str) -> None:
    """Validate station name format"""
    if not station_name or not isinstance(station_name, str):
        raise ValueError("Station name must be a non-empty string")

def validate_date_format(date_str: str) -> None:
    """Validate date format (YYYY-MM-DD)"""
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date must be a non-empty string")
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")

# ==============================================
# TICKET SEARCH FUNCTIONS
# ==============================================

@tool
def search_available_tickets(from_station: str = "", to_station: str = "",
                              departure_date: str = "", ticket_type: str = "") -> Dict:
    """
    Search available tickets for purchase (inventory system)

    Args:
        from_station (str, optional): Origin station or city name
        to_station (str, optional): Destination station or city name
        departure_date (str, optional): Date in 'YYYY-MM-DD' format (searches from this date onward)
        ticket_type (str, optional): Type of ticket to filter by

    Returns:
        dict: Available tickets for purchase (returns all matching results)
    """
    db = None
    try:
        from_station = from_station or None
        to_station = to_station or None
        departure_date = departure_date or None

        if from_station:
            validate_station_name(from_station)
        if to_station:
            validate_station_name(to_station)
        if departure_date:
            validate_date_format(departure_date)

        db = get_database_connection()

        tickets = db.search_available_tickets(
            from_station=from_station,
            to_station=to_station,
            departure_date=departure_date,
            ticket_type=None,
            max_price=None
        )

        if not tickets:
            search_desc = "available tickets"
            if from_station:
                search_desc += f" from {from_station}"
            if to_station:
                search_desc += f" to {to_station}"
            if departure_date:
                search_desc += f" on {departure_date}"
            return {"error": f"No {search_desc} found"}

        ticket_list = []
        for ticket in tickets:
            ticket_info = {
                "ticket_id": ticket["id"],
                "from_station": ticket["from_station"],
                "to_station": ticket["to_station"],
                "departure_time": ticket["departure_time"],
                "arrival_time": ticket["arrival_time"],
                "price": float(ticket["current_price"]),  # Fixed: use current_price instead of price
                "base_price": float(ticket["base_price"]),
                "current_price": float(ticket["current_price"]),
                "ticket_type": ticket["ticket_type"],
                "train_number": ticket["train_number"],
                "seat_number": ticket.get("seat_number"),
                "carriage": ticket.get("carriage"),
                "booking_class": ticket.get("booking_class"),
                "amenities": ticket.get("amenities", {}),
                "route_distance_km": ticket.get("route_distance_km")
            }
            ticket_list.append(ticket_info)

        result = {
            "success": True,
            "total_tickets": len(ticket_list),
            "search_criteria": {
                "from_station": from_station,
                "to_station": to_station,
                "departure_date": departure_date
            },
            "tickets": ticket_list
        }

        return result
    except ValueError as e:
        return {"error": str(e)}
    except sqlite3.Error as e:
        return {"success": False, "error": f"Database error: {str(e)}", "tickets": []}
    except ConnectionError as e:
        return {"success": False, "error": f"Connection error: {str(e)}", "tickets": []}
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Unexpected error in search_available_tickets")
        return {"success": False, "error": "An unexpected error occurred during search", "tickets": []}
    finally:
        if db:
            db.close()


@tool
def get_available_ticket_details(ticket_id: int = 0) -> Dict:
    """
    Get detailed information about a specific available ticket

    Args:
        ticket_id (int): The ticket ID from available inventory

    Returns:
        dict: Detailed ticket information
    """
    db = None
    try:
        if not isinstance(ticket_id, int) or ticket_id <= 0:
            raise ValueError("Ticket ID must be a positive integer")

        db = get_database_connection()
        ticket = db.get_available_ticket_details(ticket_id)

        if not ticket:
            return {"error": f"Available ticket with ID {ticket_id} not found"}

        return {
            "success": True,
            "ticket_id": ticket["id"],
            "from_station": ticket["from_station"],
            "to_station": ticket["to_station"],
            "departure_time": ticket["departure_time"],
            "arrival_time": ticket["arrival_time"],
            "price": float(ticket["current_price"]),  # Fixed: use current_price instead of price
            "base_price": float(ticket["base_price"]),
            "current_price": float(ticket["current_price"]),
            "ticket_type": ticket["ticket_type"],
            "train_number": ticket["train_number"],
            "seat_number": ticket.get("seat_number"),
            "carriage": ticket.get("carriage"),
            "booking_class": ticket.get("booking_class"),
            "amenities": ticket.get("amenities", {}),
            "route_distance_km": ticket.get("route_distance_km")
        }
    except ValueError as e:
        return {"error": str(e)}
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}
    except (KeyError, TypeError) as e:
        return {"error": f"Data processing error: {str(e)}"}
    finally:
        if db:
            db.close()


@tool
def check_seat_availability(train_number: str = "", departure_date: str = "", carriage: str = "") -> Dict:
    """
    Check seat availability for a specific train

    Args:
        train_number (str): Train number (e.g., 'UK101')
        departure_date (str): Date in 'YYYY-MM-DD' format
        carriage (str, optional): Specific carriage number

    Returns:
        dict: Seat availability information
    """
    db = None
    try:
        if not train_number or not isinstance(train_number, str):
            raise ValueError("Train number must be a non-empty string")
        validate_date_format(departure_date)

        carriage_param = carriage or None

        db = get_database_connection()
        availability = db.check_seat_availability(train_number, departure_date, carriage_param)

        if not availability:
            return {"error": f"No availability information found for train {train_number} on {departure_date}"}

        return {
            "success": True,
            "train_number": train_number,
            "departure_date": departure_date,
            "total_available_seats": availability.get("total_available", 0),
            "availability_by_carriage": availability.get("by_carriage", {}),
            "seat_details": availability.get("seat_details", [])
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if db:
            db.close()


# ==============================================
# CITY-BASED SEARCH FUNCTIONS
# ==============================================

@tool
def search_tickets_by_city(city_name: str = "", departure_date: str = "", limit: int = 20) -> Dict:
    """
    Search tickets departing from or arriving at a city

    Args:
        city_name (str): City name to search (case insensitive)
        departure_date (str, optional): Date in 'YYYY-MM-DD' format (searches from this date onward)
        limit (int): Maximum results to return

    Returns:
        dict: Available tickets from or to the specified city
    """
    if not city_name or not isinstance(city_name, str):
        return {"error": "City name must be a non-empty string"}

    departure_date = departure_date or None
    if limit <= 0:
        limit = 20

    stations = get_stations_by_city(city_name.strip())
    if not stations:
        return {"error": f"No stations found for city '{city_name}'. Please check the city name or use a specific station name."}

    # Search for tickets both from and to this city
    results = {"from_city": [], "to_city": [], "stations_searched": stations}

    # Search tickets FROM this city
    from_results = search_available_tickets.invoke({"from_station": city_name, "to_station": "", "departure_date": departure_date or "", "ticket_type": ""})
    if from_results.get("success"):
        results["from_city"] = from_results.get("tickets", [])

    # Search tickets TO this city
    to_results = search_available_tickets.invoke({"from_station": "", "to_station": city_name, "departure_date": departure_date or "", "ticket_type": ""})
    if to_results.get("success"):
        results["to_city"] = to_results.get("tickets", [])

    total_tickets = len(results["from_city"]) + len(results["to_city"])

    return {
        "success": True,
        "city_name": city_name,
        "departure_date": departure_date,
        "total_tickets_found": total_tickets,
        "tickets_from_city": len(results["from_city"]),
        "tickets_to_city": len(results["to_city"]),
        "results": results
    }


@tool
def search_tickets_from_city(from_city: str = "", departure_date: str = "", ticket_type: str = "", limit: int = 20) -> Dict:
    """
    Search tickets departing from a specific city

    Args:
        from_city (str): Origin city name
        departure_date (str, optional): Date in 'YYYY-MM-DD' format (searches from this date onward)
        ticket_type (str, optional): 'standard', 'flexible', 'first_class'
        limit (int): Maximum results to return

    Returns:
        dict: Available tickets from the specified city
    """
    departure_date = departure_date or None
    if limit <= 0:
        limit = 20

    return search_available_tickets.invoke({
        "from_station": from_city,
        "to_station": "",
        "departure_date": departure_date or "",
        "ticket_type": ""
    })


@tool
def search_tickets_to_city(to_city: str = "", departure_date: str = "", limit: int = 20) -> Dict:
    """
    Search tickets arriving at a specific city

    Args:
        to_city (str): Destination city name
        departure_date (str, optional): Date in 'YYYY-MM-DD' format (searches from this date onward)
        limit (int): Maximum results to return

    Returns:
        dict: Available tickets to the specified city
    """
    departure_date = departure_date or None
    if limit <= 0:
        limit = 20

    return search_available_tickets.invoke({
        "from_station": "",
        "to_station": to_city,
        "departure_date": departure_date or "",
        "ticket_type": ""
    })


@tool
def search_routes_between_cities(from_location: str = "", to_location: str = "", departure_date: str = "", limit: int = 20) -> Dict:
    """
    Search routes between two cities/locations

    Args:
        from_location (str): Origin city or station name
        to_location (str): Destination city or station name
        departure_date (str, optional): Date in 'YYYY-MM-DD' format
        limit (int): Maximum results to return

    Returns:
        dict: Available routes between the locations
    """
    departure_date = departure_date or None
    if limit <= 0:
        limit = 20

    return search_available_tickets.invoke({
        "from_station": from_location,
        "to_station": to_location,
        "departure_date": departure_date or "",
        "ticket_type": ""
    })


@tool
def get_location_suggestions(query: str = "") -> Dict:
    """
    Get location suggestions for cities and stations

    Args:
        query (str): Search query for location

    Returns:
        dict: Location suggestions including cities and stations
    """
    if not query or not isinstance(query, str):
        return {"error": "Query must be a non-empty string"}

    try:
        results = search_cities_and_stations(query)

        return {
            "success": True,
            "query": query,
            "cities": results["cities"],
            "stations": results["stations"],
            "suggestions": results["suggestions"],
            "total_suggestions": len(results["cities"]) + len(results["stations"])
        }
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}


# ==============================================
# BOOKING FUNCTIONS
# ==============================================

def normalize_payment_method(payment_method: str) -> str:
    """Normalize payment method input to match database constraints"""
    if not payment_method:
        return 'credit_card'

    # Convert to lowercase and replace spaces with underscores
    normalized = payment_method.lower().replace(' ', '_')

    # Map common variations to database values
    payment_method_mapping = {
        'apple_pay': 'apple_pay',
        'applepay': 'apple_pay',
        'google_pay': 'google_pay',
        'googlepay': 'google_pay',
        'credit_card': 'credit_card',
        'creditcard': 'credit_card',
        'debit_card': 'debit_card',
        'debitcard': 'debit_card',
        'paypal': 'paypal',
        'bank_transfer': 'bank_transfer',
        'banktransfer': 'bank_transfer',
        'voucher': 'voucher',
        'loyalty_points': 'loyalty_points',
        'loyaltypoints': 'loyalty_points',
        'corporate_account': 'corporate_account',
        'corporateaccount': 'corporate_account'
    }

    return payment_method_mapping.get(normalized, normalized)


@tool
def book_ticket(customer_email: str = "", ticket_id: int = 0, payment_method: str = "") -> Dict:
    """
    Book an available ticket for a customer (moves from inventory to booked)

    Args:
        customer_email (str): Customer email address
        ticket_id (int): ID of the available ticket to book
        payment_method (str): Payment method

    Returns:
        dict: Booking result with booking reference or error
    """
    db = None
    try:
        validate_email(customer_email)
        if not isinstance(ticket_id, int) or ticket_id <= 0:
            raise ValueError("Ticket ID must be a positive integer")

        # Normalize payment method
        payment_method = normalize_payment_method(payment_method)

        db = get_database_connection()
        result = db.book_ticket(customer_email, ticket_id, payment_method)

        if 'error' in result:
            return {"error": result['error']}

        return {
            "success": True,
            "booking_reference": result["booking_reference"],
            "customer_email": customer_email,
            "booked_ticket_id": result["booked_ticket_id"],
            "original_available_ticket_id": result["original_available_ticket_id"],
            "ticket_moved_from_inventory": result["ticket_moved_from_inventory"],
            "ticket_details": result["ticket_details"],
            "message": f"Ticket successfully booked! Reference: {result['booking_reference']}. Ticket ID {ticket_id} moved from available inventory to booking ID {result['booked_ticket_id']}"
        }
    except ValueError as e:
        return {"error": str(e)}
    except sqlite3.Error as e:
        return {"error": f"Database error during booking: {str(e)}"}
    except (KeyError, TypeError) as e:
        return {"error": f"Booking data error: {str(e)}"}
    finally:
        if db:
            db.close()


# ==============================================
# REFUND FUNCTIONS
# ==============================================

@tool
def refund_ticket(booking_reference: str = "", reason: str = "") -> Dict:
    """
    Process a ticket refund and return it to available inventory

    Args:
        booking_reference (str): Booking reference to refund
        reason (str): Reason for refund

    Returns:
        dict: Refund result with amount or error
    """
    db = None
    try:
        validate_booking_reference(booking_reference)

        # Handle default reason
        if not reason:
            reason = 'Customer request'

        db = get_database_connection()
        result = db.refund_ticket(booking_reference, reason)

        if 'error' in result:
            return {"error": result['error']}

        return {
            "success": True,
            "booking_reference": booking_reference,
            "refund_amount": result["refund_amount"],
            "refund_percentage": result["refund_percentage"],
            "ticket_moved_to_inventory": result["ticket_moved_to_inventory"],
            "new_available_ticket_id": result["new_available_ticket_id"],
            "booking_reference_removed": result["booking_reference_removed"],
            "message": f"Refund processed: £{result['refund_amount']} ({result['refund_percentage']}%). Ticket moved to available inventory as ID {result['new_available_ticket_id']}"
        }
    except ValueError as e:
        return {"error": str(e)}
    except sqlite3.Error as e:
        return {"error": f"Database error during refund: {str(e)}"}
    except (KeyError, TypeError) as e:
        return {"error": f"Refund data error: {str(e)}"}
    finally:
        if db:
            db.close()


@tool
def calculate_refund_amount(booking_reference: str = "") -> Dict:
    """
    Calculate refund amount for a booking without processing the refund

    Args:
        booking_reference (str): Booking reference to calculate refund for

    Returns:
        dict: Refund calculation details
    """
    db = None
    try:
        validate_booking_reference(booking_reference)

        db = get_database_connection()
        result = db.calculate_refund_amount(booking_reference)

        if 'error' in result:
            return {"error": result['error']}

        return {
            "success": True,
            "booking_reference": booking_reference,
            "original_price": result["original_price"],
            "refund_amount": result["refund_amount"],
            "refund_percentage": result["refund_percentage"],
            "cancellation_fee": result.get("cancellation_fee", 0),
            "refund_policy": result.get("refund_policy", "Standard refund policy applies"),
            "message": f"Refund calculation: £{result['refund_amount']} ({result['refund_percentage']}%) would be refunded"
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if db:
            db.close()


# ==============================================
# CUSTOMER TICKET FUNCTIONS
# ==============================================

@tool
def get_customer_bookings(email: str = "") -> Dict:
    """
    Get all bookings for a customer

    Args:
        email (str): Customer email address

    Returns:
        dict: Customer bookings information
    """
    db = None
    try:
        validate_email(email)

        db = get_database_connection()
        bookings = db.get_customer_bookings(email)

        if not bookings:
            return {"success": True, "bookings": [], "message": f"No bookings found for {email}"}

        return {
            "success": True,
            "customer_email": email,
            "total_bookings": len(bookings),
            "bookings": bookings
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if db:
            db.close()


@tool
def get_active_tickets_for_customer(email: str = "") -> Dict:
    """
    Get active tickets for a customer using their email address

    Args:
        email (str): Customer email address

    Returns:
        dict: Active tickets for the customer
    """
    db = None
    try:
        validate_email(email)

        db = get_database_connection()
        tickets = db.find_active_customer_tickets(email)

        if not tickets:
            return {"success": True, "tickets": [], "message": f"No active tickets found for {email}"}

        return {
            "success": True,
            "customer_email": email,
            "total_active_tickets": len(tickets),
            "tickets": [
                {
                    "booking_reference": ticket["booking_reference"],
                    "from_station": ticket["from_station"],
                    "to_station": ticket["to_station"],
                    "departure_time": ticket["departure_time"],
                    "estimated_arrival_time": ticket["estimated_arrival_time"],
                    "seat_number": ticket["seat_number"],
                    "carriage": ticket["carriage"],
                    "ticket_type": ticket["ticket_type"],
                    "paid_price": float(ticket["paid_price"]),
                    "train_number": ticket["train_number"],
                    "service_name": ticket.get("service_name"),
                    "operator": ticket.get("operator")
                }
                for ticket in tickets
            ]
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if db:
            db.close()


def get_all_ticket_tools() -> list:
    """Return all ticket tools as a list for agent binding."""
    return [
        search_available_tickets,
        search_tickets_from_city,
        search_tickets_to_city,
        search_tickets_by_city,
        search_routes_between_cities,
        book_ticket,
        get_customer_bookings,
        get_active_tickets_for_customer,
        refund_ticket,
        calculate_refund_amount,
        get_available_ticket_details,
        check_seat_availability,
        get_location_suggestions,
    ]
