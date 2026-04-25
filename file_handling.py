"""
file_handling.py
================
This module handles ALL file reading and writing for HotelHub.

WHY isolate file I/O here?
----------------------------
File operations are inherently risky:
  - Files might not exist (FileNotFoundError).
  - Files might be empty or malformed (ValueError, IndexError).
  - Disk could be full or permissions could be denied (OSError).

By keeping all this risk in ONE module, we:
  1. Contain all the try-except boilerplate in one place.
  2. Let the rest of the application assume clean data objects.
  3. Make it easy to swap CSV storage for a database later (just change this file).

This module has NO awareness of the menu, the GUI, or the manager's logic.
It only knows how to read/write files and return raw data structures.
"""

import csv
import os
from datetime import datetime

# Import our custom exceptions
from exceptions import DataLoadError

# ── File paths (constants so they're easy to change in one place) ──
GUESTS_FILE   = "data/guests.csv"
BOOKINGS_FILE = "data/bookings.csv"
ROOMS_FILE    = "data/rooms.csv"
REPORT_FILE   = "data/daily_occupancy_report.txt"

# ── CSV column headers ──
GUEST_FIELDS   = ["guest_id", "full_name", "email", "phone", "id_number"]
ROOM_FIELDS    = ["room_number", "room_type", "price_per_night", "status"]
BOOKING_FIELDS = [
    "booking_id", "guest_id", "room_number",
    "check_in_date", "check_out_date", "status", "total_cost"
]


def _ensure_data_directory():
    """
    Create the 'data/' folder if it doesn't exist yet.

    WHY? We don't want the program to crash if the data folder is missing.
    This runs silently before any file operation.
    """
    os.makedirs("data", exist_ok=True)  # exist_ok=True means: don't error if it exists


# ════════════════════════════════════════════════════════════════
# LOADING FUNCTIONS (Reading from disk)
# ════════════════════════════════════════════════════════════════

def load_rooms() -> list:
    """
    Load all rooms from the rooms CSV file.

    Returns a list of dictionaries, one per row. The hotel_manager will
    then convert these dicts into Room objects.

    Returns
    -------
    list of dict
        Each dict has keys: room_number, room_type, price_per_night, status.
        Returns an empty list if the file doesn't exist or is empty.
    """
    _ensure_data_directory()

    # ── GRACEFUL STARTUP: if no file, return empty list (not a crash) ──
    if not os.path.exists(ROOMS_FILE):
        print(f"[Info] '{ROOMS_FILE}' not found. Starting with empty room inventory.")
        return []

    rooms = []
    try:
        with open(ROOMS_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=2):  # start=2: row 1 is header
                try:
                    # Validate that required fields exist in this row
                    _check_row_fields(row, ROOM_FIELDS, ROOMS_FILE, row_number)
                    rooms.append(dict(row))
                except DataLoadError as e:
                    # Log the bad row and SKIP it instead of crashing
                    print(f"[Warning] Skipping malformed row {row_number} in rooms file: {e}")
    except OSError as e:
        print(f"[Warning] Could not read '{ROOMS_FILE}': {e}. Starting with no rooms.")

    return rooms


def load_guests() -> list:
    """
    Load all guests from the guests CSV file.

    Returns
    -------
    list of dict
        Each dict has keys: guest_id, full_name, email, phone, id_number.
        Returns an empty list if the file doesn't exist.
    """
    _ensure_data_directory()

    if not os.path.exists(GUESTS_FILE):
        print(f"[Info] '{GUESTS_FILE}' not found. Starting with no guest records.")
        return []

    guests = []
    try:
        with open(GUESTS_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=2):
                try:
                    _check_row_fields(row, GUEST_FIELDS, GUESTS_FILE, row_number)
                    guests.append(dict(row))
                except DataLoadError as e:
                    print(f"[Warning] Skipping malformed row {row_number} in guests file: {e}")
    except OSError as e:
        print(f"[Warning] Could not read '{GUESTS_FILE}': {e}. Starting with no guests.")

    return guests


def load_bookings() -> list:
    """
    Load all bookings from the bookings CSV file.

    Returns
    -------
    list of dict
        Each dict has keys: booking_id, guest_id, room_number,
        check_in_date, check_out_date, status, total_cost.
        Returns an empty list if the file doesn't exist.
    """
    _ensure_data_directory()

    if not os.path.exists(BOOKINGS_FILE):
        print(f"[Info] '{BOOKINGS_FILE}' not found. Starting with no bookings.")
        return []

    bookings = []
    try:
        with open(BOOKINGS_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=2):
                try:
                    _check_row_fields(row, BOOKING_FIELDS, BOOKINGS_FILE, row_number)
                    bookings.append(dict(row))
                except DataLoadError as e:
                    print(f"[Warning] Skipping malformed row {row_number} in bookings file: {e}")
    except OSError as e:
        print(f"[Warning] Could not read '{BOOKINGS_FILE}': {e}. Starting with no bookings.")

    return bookings


# ════════════════════════════════════════════════════════════════
# SAVING FUNCTIONS (Writing to disk)
# ════════════════════════════════════════════════════════════════

def save_rooms(rooms: list):
    """
    Overwrite the rooms CSV with the current list of Room objects.

    Parameters
    ----------
    rooms : list of Room
        All Room objects from the hotel manager.
    """
    _ensure_data_directory()
    _write_csv(
        filepath=ROOMS_FILE,
        fieldnames=ROOM_FIELDS,
        rows=[room.get_info() for room in rooms],
    )


def save_guests(guests: list):
    """
    Overwrite the guests CSV with the current list of Guest objects.

    Parameters
    ----------
    guests : list of Guest
        All Guest objects from the hotel manager.
    """
    _ensure_data_directory()
    _write_csv(
        filepath=GUESTS_FILE,
        fieldnames=GUEST_FIELDS,
        rows=[guest.to_dict() for guest in guests],
    )


def save_bookings(bookings: list):
    """
    Overwrite the bookings CSV with the current list of Booking objects.

    Parameters
    ----------
    bookings : list of Booking
        All Booking objects from the hotel manager.
    """
    _ensure_data_directory()
    _write_csv(
        filepath=BOOKINGS_FILE,
        fieldnames=BOOKING_FIELDS,
        rows=[booking.to_dict() for booking in bookings],
    )


def export_daily_report(rooms: list, bookings: list):
    """
    Write a human-readable daily occupancy report to a .txt file.

    This gives the hotel owner a quick snapshot they can print or email.

    Parameters
    ----------
    rooms : list of Room
        All Room objects.
    bookings : list of Booking
        All Booking objects.
    """
    _ensure_data_directory()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    # ── Header ──
    lines.append("=" * 60)
    lines.append("       HOTELHUB — DAILY OCCUPANCY REPORT")
    lines.append(f"       Generated: {now}")
    lines.append("=" * 60)
    lines.append("")

    # ── Room Status Summary ──
    available_rooms = [r for r in rooms if r.is_available()]
    occupied_rooms  = [r for r in rooms if r.status == "occupied"]
    reserved_rooms  = [r for r in rooms if r.status == "reserved"]

    lines.append(f"Total Rooms   : {len(rooms)}")
    lines.append(f"  Available   : {len(available_rooms)}")
    lines.append(f"  Occupied    : {len(occupied_rooms)}")
    lines.append(f"  Reserved    : {len(reserved_rooms)}")
    lines.append("")

    # ── Room Details Table ──
    lines.append("-" * 60)
    lines.append(f"{'Room':<8} {'Type':<10} {'Price/Night':<14} {'Status'}")
    lines.append("-" * 60)
    for room in sorted(rooms, key=lambda r: r.room_number):
        info = room.get_info()
        lines.append(
            f"{info['room_number']:<8} {info['room_type']:<10} "
            f"${info['price_per_night']:<13.2f} {info['status'].upper()}"
        )
    lines.append("")

    # ── Active Bookings Section ──
    active = [b for b in bookings if b.status not in ("cancelled", "checked_out")]
    lines.append("-" * 60)
    lines.append(f"Active Bookings: {len(active)}")
    lines.append("-" * 60)
    for booking in active:
        lines.append(str(booking))
    lines.append("")
    lines.append("=" * 60)
    lines.append("End of Report")

    # ── Write to file ──
    try:
        with open(REPORT_FILE, mode="w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[Success] Daily report saved to '{REPORT_FILE}'.")
    except OSError as e:
        print(f"[Error] Could not write report: {e}")


# ════════════════════════════════════════════════════════════════
# PRIVATE HELPERS (not meant to be called from outside this module)
# ════════════════════════════════════════════════════════════════

def _write_csv(filepath: str, fieldnames: list, rows: list):
    """
    Generic helper to write a list of dicts to a CSV file.

    Parameters
    ----------
    filepath : str
        Path to write the file.
    fieldnames : list of str
        Column headers.
    rows : list of dict
        Data rows to write.
    """
    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        # Log but don't crash — data is still in memory even if save fails
        print(f"[Error] Could not save to '{filepath}': {e}")


def _check_row_fields(row: dict, required_fields: list, filename: str, row_num: int):
    """
    Verify that a CSV row contains all required fields (non-empty).

    Parameters
    ----------
    row : dict
        The row from csv.DictReader.
    required_fields : list
        The expected column names.
    filename : str
        Used in the error message.
    row_num : int
        Used in the error message.

    Raises
    ------
    DataLoadError
        If any required field is missing or empty.
    """
    for field in required_fields:
        if field not in row or not str(row[field]).strip():
            raise DataLoadError(
                filename=filename,
                detail=f"Row {row_num} is missing or has empty field '{field}'.",
            )
