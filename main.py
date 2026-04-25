"""
main.py
=======
The Command-Line Interface (CLI) entry point for HotelHub.

IMPORTANT DESIGN RULE — Zero Business Logic Here
-------------------------------------------------
This file is ONLY responsible for:
  1. Displaying menus to the user.
  2. Collecting user input via input().
  3. Calling the appropriate HotelManager method.
  4. Displaying results or error messages.

ALL business logic (date conflicts, billing, state transitions) lives inside
the HotelManager and the domain classes. This keeps main.py clean and short.

If you find yourself writing an `if/else` that isn't about menu navigation,
that logic belongs in hotel_manager.py or the classes, not here.
"""

# ── Standard library ──
import sys

# ── Our modules ──
from hotel_manager import HotelManager
from reporting import (
    generate_occupancy_report,
    generate_guest_report,
    generate_billing_summary,
    generate_bookings_in_range,
)
from exceptions import HotelHubError
from validation import validate_date_range, validate_positive_number


# ════════════════════════════════════════════════════════════════
# HELPER UTILITIES (pure I/O helpers — no business logic)
# ════════════════════════════════════════════════════════════════

def clear_screen():
    """Print blank lines to simulate clearing the terminal."""
    print("\n" * 2)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "─" * 55)
    print(f"  {title}")
    print("─" * 55)


def prompt(label: str) -> str:
    """
    Prompt the user for input and return the stripped result.

    WHY strip()?
    ------------
    Users often accidentally add spaces before or after their input.
    .strip() removes that whitespace so "101 " and "101" are treated the same.
    """
    return input(f"  {label}: ").strip()


def confirm(message: str) -> bool:
    """Ask the user a yes/no question. Returns True if they answer 'y'."""
    answer = input(f"  {message} (y/n): ").strip().lower()
    return answer == "y"


# ════════════════════════════════════════════════════════════════
# ROOM MENU HANDLERS
# ════════════════════════════════════════════════════════════════

def menu_add_room(manager: HotelManager):
    """Handle the 'Add Room' workflow."""
    print_header("ADD NEW ROOM")
    try:
        room_number    = prompt("Room number (e.g., 101)")
        room_type      = prompt("Room type (single / double / suite)")
        price_str      = prompt("Price per night (e.g., 120.00)")
        price_per_night = validate_positive_number(price_str, "Price per night")

        room = manager.add_room(room_number, room_type, price_per_night)
        print(f"\n  ✅ Room added successfully!\n  {room}")

    except HotelHubError as e:
        # Catch any of our custom exceptions and show a friendly message
        print(f"\n  ❌ {e}")
    except ValueError as e:
        print(f"\n  ❌ Invalid input: {e}")


def menu_view_rooms(manager: HotelManager):
    """Display all rooms with their current status."""
    print_header("ALL ROOMS")
    rooms = manager.get_all_rooms()
    if not rooms:
        print("  No rooms in the system yet.")
        return
    for room in rooms:
        icon = {"available": "✅", "occupied": "🔴", "reserved": "🟡"}.get(room.status, "❓")
        print(f"  {icon} {room}")


def menu_view_available_rooms(manager: HotelManager):
    """Display only available rooms."""
    print_header("AVAILABLE ROOMS")
    rooms = manager.get_available_rooms()
    if not rooms:
        print("  No rooms are currently available.")
        return
    for room in rooms:
        print(f"  ✅ {room}")


# ════════════════════════════════════════════════════════════════
# GUEST MENU HANDLERS
# ════════════════════════════════════════════════════════════════

def menu_register_guest(manager: HotelManager):
    """Handle the 'Register Guest' workflow."""
    print_header("REGISTER NEW GUEST")
    try:
        full_name = prompt("Full name")
        email     = prompt("Email address")
        phone     = prompt("Phone number (digits only)")
        id_number = prompt("ID / Passport number")

        guest = manager.register_guest(full_name, email, phone, id_number)
        print(f"\n  ✅ Guest registered!\n  {guest}")
        print(f"  ℹ️  Guest ID: {guest.guest_id} (save this for bookings)")

    except HotelHubError as e:
        print(f"\n  ❌ {e}")
    except ValueError as e:
        print(f"\n  ❌ Invalid input: {e}")


def menu_view_guests(manager: HotelManager):
    """Display all registered guests."""
    print_header("ALL GUESTS")
    guests = manager.get_all_guests()
    if not guests:
        print("  No guests registered yet.")
        return
    for guest in guests:
        print(f"  👤 {guest}")


def menu_find_guest(manager: HotelManager):
    """Search for a guest by name."""
    print_header("FIND GUEST BY NAME")
    try:
        query   = prompt("Enter name to search")
        results = manager.find_guest_by_name(query)
        if not results:
            print(f"  No guests found matching '{query}'.")
        else:
            for guest in results:
                print(f"  👤 {guest}")
    except Exception as e:
        print(f"\n  ❌ {e}")


def menu_guest_history(manager: HotelManager):
    """Show full booking history for a guest."""
    print_header("GUEST BOOKING HISTORY")
    try:
        guest_id = prompt("Enter Guest ID (e.g., G-001)")
        guest    = manager.get_guest(guest_id)
        bookings = manager.get_all_bookings()
        report   = generate_guest_report(guest, bookings)
        print(report)
    except HotelHubError as e:
        print(f"\n  ❌ {e}")


# ════════════════════════════════════════════════════════════════
# BOOKING MENU HANDLERS
# ════════════════════════════════════════════════════════════════

def menu_create_booking(manager: HotelManager):
    """Handle the 'Create Booking' workflow."""
    print_header("CREATE NEW BOOKING")
    try:
        guest_id    = prompt("Guest ID (e.g., G-001)")
        room_number = prompt("Room number (e.g., 101)")
        check_in    = prompt("Check-in date (YYYY-MM-DD)")
        check_out   = prompt("Check-out date (YYYY-MM-DD)")

        # Validate dates before sending to manager
        check_in_date, check_out_date = validate_date_range(check_in, check_out)

        booking = manager.create_booking(
            guest_id       = guest_id,
            room_number    = room_number,
            check_in_date  = check_in_date,
            check_out_date = check_out_date,
        )
        print(f"\n  ✅ Booking created successfully!")
        print(f"  {booking}")
        print(generate_billing_summary(booking))

    except HotelHubError as e:
        print(f"\n  ❌ {e}")
    except ValueError as e:
        print(f"\n  ❌ Invalid input: {e}")


def menu_view_bookings(manager: HotelManager):
    """Display all bookings in the system."""
    print_header("ALL BOOKINGS")
    bookings = manager.get_all_bookings()
    if not bookings:
        print("  No bookings in the system yet.")
        return
    for booking in bookings:
        print(f"  📋 {booking}")


def menu_check_in(manager: HotelManager):
    """Handle the check-in workflow for an existing booking."""
    print_header("GUEST CHECK-IN")
    try:
        booking_id = prompt("Booking ID (e.g., BK-001)")
        booking    = manager.check_in_guest(booking_id)
        print(f"\n  ✅ Check-in successful! Room {booking.room.room_number} is now OCCUPIED.")
        print(f"  {booking}")
    except HotelHubError as e:
        print(f"\n  ❌ {e}")


def menu_check_out(manager: HotelManager):
    """Handle the check-out workflow — show final bill."""
    print_header("GUEST CHECK-OUT")
    try:
        booking_id = prompt("Booking ID (e.g., BK-001)")
        booking    = manager.check_out_guest(booking_id)
        print(f"\n  ✅ Check-out successful! Room {booking.room.room_number} is now AVAILABLE.")
        print(generate_billing_summary(booking))
    except HotelHubError as e:
        print(f"\n  ❌ {e}")


def menu_cancel_booking(manager: HotelManager):
    """Handle booking cancellation."""
    print_header("CANCEL BOOKING")
    try:
        booking_id = prompt("Booking ID to cancel (e.g., BK-001)")

        # Show the booking first so the user knows what they're cancelling
        booking = manager.get_booking(booking_id)
        print(f"\n  Booking to cancel:\n  {booking}")

        if confirm("Are you sure you want to cancel this booking?"):
            manager.cancel_booking(booking_id)
            print(f"\n  ✅ Booking {booking_id} has been cancelled. Room is now available.")
        else:
            print("  Cancellation aborted.")

    except HotelHubError as e:
        print(f"\n  ❌ {e}")


def menu_bookings_by_date(manager: HotelManager):
    """Show bookings within a date range."""
    print_header("BOOKINGS BY DATE RANGE")
    try:
        start_str = prompt("Start date (YYYY-MM-DD)")
        end_str   = prompt("End date (YYYY-MM-DD)")
        start, end = validate_date_range(start_str, end_str)

        bookings = manager.get_bookings_in_range(start, end)
        report   = generate_bookings_in_range(manager.get_all_bookings(), start, end)
        print(report)

    except HotelHubError as e:
        print(f"\n  ❌ {e}")
    except ValueError as e:
        print(f"\n  ❌ {e}")


# ════════════════════════════════════════════════════════════════
# REPORTING MENU HANDLERS
# ════════════════════════════════════════════════════════════════

def menu_occupancy_report(manager: HotelManager):
    """Show the full room occupancy report."""
    rooms    = manager.get_all_rooms()
    bookings = manager.get_all_bookings()
    print(generate_occupancy_report(rooms, bookings))


def menu_export_report(manager: HotelManager):
    """Export the daily occupancy report to a text file."""
    print_header("EXPORT DAILY REPORT")
    manager.export_report()


# ════════════════════════════════════════════════════════════════
# MAIN MENU DISPLAY
# ════════════════════════════════════════════════════════════════

def display_main_menu():
    """Print the main menu options to the terminal."""
    print("""
╔══════════════════════════════════════════════════╗
║            HOTELHUB — MAIN MENU                  ║
╠══════════════════════════════════════════════════╣
║  ROOMS                                           ║
║   1. Add a new room                              ║
║   2. View all rooms                              ║
║   3. View available rooms                        ║
╠══════════════════════════════════════════════════╣
║  GUESTS                                          ║
║   4. Register a new guest                        ║
║   5. View all guests                             ║
║   6. Find guest by name                          ║
║   7. View guest booking history                  ║
╠══════════════════════════════════════════════════╣
║  BOOKINGS                                        ║
║   8.  Create a booking                           ║
║   9.  View all bookings                          ║
║   10. Check-in guest                             ║
║   11. Check-out guest                            ║
║   12. Cancel a booking                           ║
║   13. View bookings by date range                ║
╠══════════════════════════════════════════════════╣
║  REPORTS                                         ║
║   14. Occupancy report                           ║
║   15. Export daily report to file                ║
╠══════════════════════════════════════════════════╣
║   0. Exit                                        ║
╚══════════════════════════════════════════════════╝""")


# ════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    """
    The main function — entry point of the CLI application.

    Creates a HotelManager (which loads all saved data) and then runs
    the menu loop until the user chooses to exit.

    WHY while True?
    ---------------
    We want the menu to keep showing after each action until the user
    explicitly chooses to quit. `while True` with a `break` on exit is
    the standard pattern for interactive CLI loops.
    """
    print("\n" + "═" * 55)
    print("   Welcome to HotelHub — Hotel Management System")
    print("═" * 55)
    print("  Loading data, please wait...")

    # Create the manager — this triggers data loading from CSV files
    manager = HotelManager()

    print("  ✅ System ready!\n")

    # Menu dispatch table: maps choice strings to handler functions.
    # WHY a dictionary instead of a giant if/elif chain?
    # A dict is cleaner, easier to extend, and avoids deeply nested conditionals.
    menu_actions = {
        "1":  menu_add_room,
        "2":  menu_view_rooms,
        "3":  menu_view_available_rooms,
        "4":  menu_register_guest,
        "5":  menu_view_guests,
        "6":  menu_find_guest,
        "7":  menu_guest_history,
        "8":  menu_create_booking,
        "9":  menu_view_bookings,
        "10": menu_check_in,
        "11": menu_check_out,
        "12": menu_cancel_booking,
        "13": menu_bookings_by_date,
        "14": menu_occupancy_report,
        "15": menu_export_report,
    }

    # ── Main menu loop ──
    while True:
        display_main_menu()

        try:
            choice = input("\n  Enter your choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C gracefully
            print("\n\n  Goodbye! Thank you for using HotelHub. 🏨")
            sys.exit(0)

        if choice == "0":
            print("\n  Goodbye! Thank you for using HotelHub. 🏨\n")
            break

        elif choice in menu_actions:
            # Look up and call the matching handler function
            # Notice: we pass `manager` as an argument — the handler does the work
            menu_actions[choice](manager)
            input("\n  Press Enter to return to the main menu...")

        else:
            print(f"\n  ⚠️  '{choice}' is not a valid option. Please choose 0–15.")


# ── Standard Python guard: only run main() if this file is executed directly ──
# If another module imports main.py (unlikely but possible), main() won't run.
if __name__ == "__main__":
    main()
