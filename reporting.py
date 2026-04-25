"""
reporting.py
============
This module generates all textual reports and summaries for the hotel.

WHY a separate reporting module?
----------------------------------
Report generation is pure READ-ONLY logic — it never changes any data.
By separating it from the manager (which writes data) and from main.py
(which handles user interaction), we keep each file laser-focused on
one job. This also means the Streamlit GUI can import these same report
functions to display charts and summaries.
"""

from datetime import date


def generate_occupancy_report(rooms: list, bookings: list) -> str:
    """
    Generate a formatted occupancy report for all rooms.

    Parameters
    ----------
    rooms : list of Room
        All room objects from the hotel manager.
    bookings : list of Booking
        All booking objects.

    Returns
    -------
    str
        A multiline string report ready to print or display.
    """
    lines = []
    lines.append("\n" + "=" * 65)
    lines.append("              ROOM OCCUPANCY REPORT")
    lines.append("=" * 65)

    # Count rooms by status
    available = [r for r in rooms if r.status == "available"]
    occupied  = [r for r in rooms if r.status == "occupied"]
    reserved  = [r for r in rooms if r.status == "reserved"]

    lines.append(f"  Total Rooms : {len(rooms)}")
    lines.append(f"  ✅ Available : {len(available)}")
    lines.append(f"  🔴 Occupied  : {len(occupied)}")
    lines.append(f"  🟡 Reserved  : {len(reserved)}")

    if rooms:
        occupancy_pct = (len(occupied) + len(reserved)) / len(rooms) * 100
        lines.append(f"  📊 Occupancy : {occupancy_pct:.1f}%")

    lines.append("")
    lines.append(f"  {'Room':<8} {'Type':<10} {'Price/Night':<14} {'Status'}")
    lines.append("  " + "-" * 50)

    for room in sorted(rooms, key=lambda r: r.room_number):
        info = room.get_info()
        status_icon = {"available": "✅", "occupied": "🔴", "reserved": "🟡"}.get(
            info["status"], "❓"
        )
        lines.append(
            f"  {info['room_number']:<8} {info['room_type']:<10} "
            f"${info['price_per_night']:<13.2f} {status_icon} {info['status'].upper()}"
        )

    lines.append("=" * 65)
    return "\n".join(lines)


def generate_guest_report(guest, bookings: list) -> str:
    """
    Generate a full booking history report for one guest.

    Parameters
    ----------
    guest : Guest
        The guest to report on.
    bookings : list of Booking
        The complete list of all bookings (will be filtered).

    Returns
    -------
    str
        A formatted multiline string.
    """
    guest_bookings = guest.get_booking_history(bookings)

    lines = []
    lines.append("\n" + "=" * 65)
    lines.append(f"  BOOKING HISTORY — {guest.full_name.upper()}")
    lines.append(f"  Guest ID: {guest.guest_id}  |  Email: {guest.email}")
    lines.append("=" * 65)

    if not guest_bookings:
        lines.append("  No bookings found for this guest.")
    else:
        total_spent = 0.0
        for b in guest_bookings:
            lines.append(f"\n  {b}")
            total_spent += b.calculate_total()
        lines.append(f"\n  ──────────────────────────────────────────────────")
        lines.append(f"  Total bookings : {len(guest_bookings)}")
        lines.append(f"  Total spent    : ${total_spent:.2f}")

    lines.append("=" * 65)
    return "\n".join(lines)


def generate_billing_summary(booking) -> str:
    """
    Generate a detailed billing invoice for a single booking.

    Parameters
    ----------
    booking : Booking
        The booking to invoice.

    Returns
    -------
    str
        A formatted billing summary string.
    """
    nights = booking.duration_nights()
    rate   = booking.room.price_per_night
    total  = booking.calculate_total()

    lines = []
    lines.append("\n" + "=" * 50)
    lines.append("          HOTELHUB — BILLING SUMMARY")
    lines.append("=" * 50)
    lines.append(f"  Booking ID    : {booking.booking_id}")
    lines.append(f"  Guest         : {booking.guest.full_name}")
    lines.append(f"  Room          : {booking.room.room_number} ({booking.room.room_type})")
    lines.append(f"  Check-in      : {booking.check_in_date}")
    lines.append(f"  Check-out     : {booking.check_out_date}")
    lines.append(f"  Duration      : {nights} night(s)")
    lines.append(f"  Rate/Night    : ${rate:.2f}")
    lines.append(f"  ─────────────────────────────────────────")
    lines.append(f"  TOTAL AMOUNT  : ${total:.2f}")
    lines.append(f"  Status        : {booking.status.upper()}")
    lines.append("=" * 50)
    return "\n".join(lines)


def generate_bookings_in_range(bookings: list, start_date: date, end_date: date) -> str:
    """
    List all bookings that overlap with a given date range.

    Parameters
    ----------
    bookings : list of Booking
        All bookings to search through.
    start_date : date
        Start of the query range.
    end_date : date
        End of the query range.

    Returns
    -------
    str
        A formatted report of overlapping bookings.
    """
    # Filter bookings that overlap with the given range
    matches = [b for b in bookings if b.overlaps_with(start_date, end_date)]

    lines = []
    lines.append("\n" + "=" * 65)
    lines.append(f"  BOOKINGS FROM {start_date} TO {end_date}")
    lines.append("=" * 65)

    if not matches:
        lines.append("  No bookings found in this date range.")
    else:
        for b in matches:
            lines.append(f"  {b}")

    lines.append(f"\n  Total found: {len(matches)}")
    lines.append("=" * 65)
    return "\n".join(lines)


def get_room_type_stats(rooms: list) -> dict:
    """
    Count the number of rooms per type and their occupancy.

    Useful for the Streamlit pie chart.

    Parameters
    ----------
    rooms : list of Room

    Returns
    -------
    dict
        Structure: {room_type: {"total": int, "occupied": int, "available": int}}
    """
    stats = {}
    for room in rooms:
        rt = room.room_type
        if rt not in stats:
            stats[rt] = {"total": 0, "occupied": 0, "available": 0, "reserved": 0}
        stats[rt]["total"] += 1
        if room.status == "occupied":
            stats[rt]["occupied"] += 1
        elif room.status == "available":
            stats[rt]["available"] += 1
        elif room.status == "reserved":
            stats[rt]["reserved"] += 1
    return stats
