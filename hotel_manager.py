"""
hotel_manager.py
================
This module contains the HotelManager class — the single source of truth for
all hotel data and cross-entity business logic.

WHAT is a "Manager" class?
----------------------------
A manager class is a pattern that acts as a coordinator for a group of related
objects. Instead of having floating functions scattered across files, ALL
operations that involve multiple classes (e.g., "create a Booking that links a
Guest to a Room") live here.

Think of HotelManager as the hotel's front desk: it knows about all rooms,
all guests, and all bookings, and it makes sure that operations are valid
before carrying them out.

This class replaces standalone utility functions and keeps main.py clean.
"""

from classes import Room, Guest, Booking, BOOKING_CONFIRMED
from exceptions import (
    RoomNotFoundError,
    RoomAlreadyExistsError,
    GuestNotFoundError,
    BookingNotFoundError,
    BookingConflictError,
    InvalidStateError,
)
from file_handling import (
    load_rooms, load_guests, load_bookings,
    save_rooms, save_guests, save_bookings,
    export_daily_report,
)


class HotelManager:
    """
    Central coordinator for all HotelHub data and operations.

    Stores rooms, guests, and bookings in dictionaries keyed by their
    unique IDs. Dictionaries are used (instead of lists) for O(1) lookups —
    finding room "101" is instant, no looping required.

    Attributes
    ----------
    _rooms    : dict {room_number: Room}
    _guests   : dict {guest_id:    Guest}
    _bookings : dict {booking_id:  Booking}
    _next_guest_number   : int (auto-increment counter for guest IDs)
    _next_booking_number : int (auto-increment counter for booking IDs)
    """

    def __init__(self):
        """
        Initialise the manager and load any existing data from CSV files.

        WHY load on __init__?
        ----------------------
        When the program starts (either CLI or Streamlit), the manager is
        created once and immediately populated with saved data. This means
        every session continues where the last one left off.
        """
        # Private storage dictionaries
        self._rooms    = {}
        self._guests   = {}
        self._bookings = {}

        # Auto-increment counters (will be updated when existing data loads)
        self._next_guest_number   = 1
        self._next_booking_number = 1

        # Load all data from disk
        self._load_all_data()

    # ════════════════════════════════════════════════════════════════
    # DATA LOADING (called once at startup)
    # ════════════════════════════════════════════════════════════════

    def _load_all_data(self):
        """
        Load rooms, guests, and bookings from CSV files and rebuild objects.

        WHY rebuild objects instead of storing raw dicts?
        --------------------------------------------------
        Our system depends on having REAL Room, Guest, Booking objects with
        methods. CSV files only store raw text. This method bridges that gap
        by reading the text and reconstructing proper objects.
        """
        # ── Load Rooms ──
        for row in load_rooms():
            try:
                room = Room(
                    room_number    = row["room_number"],
                    room_type      = row["room_type"],
                    price_per_night= float(row["price_per_night"]),
                )
                # Restore the saved status (it might be occupied or reserved)
                room._status = row.get("status", "available")
                self._rooms[room.room_number] = room
            except (ValueError, KeyError) as e:
                print(f"[Warning] Skipping invalid room data: {e}")

        # ── Load Guests ──
        for row in load_guests():
            try:
                guest = Guest(
                    guest_id  = row["guest_id"],
                    full_name = row["full_name"],
                    email     = row["email"],
                    phone     = row["phone"],
                    id_number = row["id_number"],
                )
                self._guests[guest.guest_id] = guest

                # Update counter so new IDs don't clash with loaded ones
                num_part = int(guest.guest_id.replace("G-", "").replace("G", ""))
                if num_part >= self._next_guest_number:
                    self._next_guest_number = num_part + 1
            except (ValueError, KeyError) as e:
                print(f"[Warning] Skipping invalid guest data: {e}")

        # ── Load Bookings ──
        # Bookings must be loaded AFTER rooms and guests because they
        # reference Room and Guest objects by ID
        for row in load_bookings():
            try:
                guest = self._guests.get(row["guest_id"])
                room  = self._rooms.get(row["room_number"])

                if not guest:
                    print(f"[Warning] Booking '{row['booking_id']}' references unknown guest '{row['guest_id']}'. Skipping.")
                    continue
                if not room:
                    print(f"[Warning] Booking '{row['booking_id']}' references unknown room '{row['room_number']}'. Skipping.")
                    continue

                booking = Booking(
                    booking_id    = row["booking_id"],
                    guest         = guest,
                    room          = room,
                    check_in_date = row["check_in_date"],
                    check_out_date= row["check_out_date"],
                )
                # Restore the saved status
                booking._status = row.get("status", BOOKING_CONFIRMED)
                self._bookings[booking.booking_id] = booking

                # Update counter
                num_part = int(row["booking_id"].replace("BK-", "").replace("BK", ""))
                if num_part >= self._next_booking_number:
                    self._next_booking_number = num_part + 1

            except (ValueError, KeyError) as e:
                print(f"[Warning] Skipping invalid booking data: {e}")

    # ════════════════════════════════════════════════════════════════
    # ID GENERATION HELPERS
    # ════════════════════════════════════════════════════════════════

    def _generate_guest_id(self) -> str:
        """Create the next sequential guest ID (e.g., 'G-001')."""
        gid = f"G-{self._next_guest_number:03d}"
        self._next_guest_number += 1
        return gid

    def _generate_booking_id(self) -> str:
        """Create the next sequential booking ID (e.g., 'BK-001')."""
        bid = f"BK-{self._next_booking_number:03d}"
        self._next_booking_number += 1
        return bid

    # ════════════════════════════════════════════════════════════════
    # ROOM OPERATIONS
    # ════════════════════════════════════════════════════════════════

    def add_room(self, room_number: str, room_type: str, price_per_night: float) -> Room:
        """
        Add a new room to the hotel inventory.

        Parameters
        ----------
        room_number : str
        room_type : str
        price_per_night : float

        Returns
        -------
        Room
            The newly created Room object.

        Raises
        ------
        RoomAlreadyExistsError
            If a room with that number already exists.
        ValueError
            If room type or price is invalid.
        """
        room_number = str(room_number).strip()

        # Guard: prevent duplicate room numbers
        if room_number in self._rooms:
            raise RoomAlreadyExistsError(room_number)

        # Create and store the room
        room = Room(room_number, room_type, price_per_night)
        self._rooms[room_number] = room

        # Immediately persist to disk
        save_rooms(list(self._rooms.values()))
        return room

    def get_room(self, room_number: str) -> Room:
        """
        Retrieve a Room object by its room number.

        Raises
        ------
        RoomNotFoundError
            If the room number doesn't exist.
        """
        room_number = str(room_number).strip()
        if room_number not in self._rooms:
            raise RoomNotFoundError(room_number)
        return self._rooms[room_number]

    def get_all_rooms(self) -> list:
        """Return all rooms as a sorted list (sorted by room number)."""
        return sorted(self._rooms.values(), key=lambda r: r.room_number)

    def get_available_rooms(self) -> list:
        """Return only rooms that are currently available."""
        return [r for r in self._rooms.values() if r.is_available()]

    # ════════════════════════════════════════════════════════════════
    # GUEST OPERATIONS
    # ════════════════════════════════════════════════════════════════

    def register_guest(
        self,
        full_name: str,
        email: str,
        phone: str,
        id_number: str,
    ) -> Guest:
        """
        Register a new guest and return the created Guest object.

        The guest ID is auto-generated (e.g., G-001, G-002, ...).

        Parameters
        ----------
        full_name : str
        email : str
        phone : str
        id_number : str

        Returns
        -------
        Guest
            The new Guest object.

        Raises
        ------
        InvalidEmailError
            If the email format is wrong.
        InvalidPhoneError
            If the phone format is wrong.
        ValueError
            If name or id_number is empty.
        """
        guest_id = self._generate_guest_id()
        guest    = Guest(guest_id, full_name, email, phone, id_number)
        self._guests[guest_id] = guest
        save_guests(list(self._guests.values()))
        return guest

    def get_guest(self, guest_id: str) -> Guest:
        """
        Retrieve a Guest by their ID.

        Raises
        ------
        GuestNotFoundError
        """
        guest_id = str(guest_id).strip()
        if guest_id not in self._guests:
            raise GuestNotFoundError(guest_id)
        return self._guests[guest_id]

    def get_all_guests(self) -> list:
        """Return all guests sorted by their ID."""
        return sorted(self._guests.values(), key=lambda g: g.guest_id)

    def find_guest_by_name(self, name_query: str) -> list:
        """
        Search for guests by partial name match (case-insensitive).

        Parameters
        ----------
        name_query : str
            Part of the guest's name to search for.

        Returns
        -------
        list of Guest
        """
        query = name_query.strip().lower()
        return [g for g in self._guests.values() if query in g.full_name.lower()]

    # ════════════════════════════════════════════════════════════════
    # BOOKING OPERATIONS
    # ════════════════════════════════════════════════════════════════

    def create_booking(
        self,
        guest_id: str,
        room_number: str,
        check_in_date,
        check_out_date,
    ) -> "Booking":
        """
        Create a new booking after checking for conflicts.

        This is the most important cross-entity operation: it links a Guest
        to a Room and checks that no existing booking blocks the dates.

        Parameters
        ----------
        guest_id : str
        room_number : str
        check_in_date : str or date
        check_out_date : str or date

        Returns
        -------
        Booking
            The newly created Booking object.

        Raises
        ------
        GuestNotFoundError
            If the guest ID doesn't exist.
        RoomNotFoundError
            If the room number doesn't exist.
        BookingConflictError
            If the dates clash with an existing booking for the same room.
        InvalidDateRangeError
            If the dates are logically invalid.
        """
        # Look up the guest and room — raises errors if not found
        guest = self.get_guest(guest_id)
        room  = self.get_room(room_number)

        # ── Check for date conflicts ──
        # We loop through ALL existing bookings for this room
        for existing_booking in self._bookings.values():
            if existing_booking.room.room_number != room_number:
                continue  # Different room, skip

            # Ask the existing booking if it overlaps with our requested range
            from classes import Booking as BookingClass
            check_in  = BookingClass._parse_date(check_in_date)
            check_out = BookingClass._parse_date(check_out_date)

            if existing_booking.overlaps_with(check_in, check_out):
                raise BookingConflictError(
                    room_number=room_number,
                    conflict_booking_id=existing_booking.booking_id,
                )

        # ── No conflict — create the booking ──
        booking_id = self._generate_booking_id()
        booking    = Booking(booking_id, guest, room, check_in_date, check_out_date)

        # NOTE: We do NOT change the room's physical status here.
        # Room status (available / occupied) reflects PHYSICAL reality only.
        # A room may have many future confirmed bookings while still being
        # physically available. Status only changes on actual check_in() /
        # check_out(). The conflict-detection above prevents double-booking.

        self._bookings[booking_id] = booking
        save_bookings(list(self._bookings.values()))
        return booking

    def get_booking(self, booking_id: str) -> "Booking":
        """
        Retrieve a Booking by its ID.

        Raises
        ------
        BookingNotFoundError
        """
        booking_id = str(booking_id).strip()
        if booking_id not in self._bookings:
            raise BookingNotFoundError(booking_id)
        return self._bookings[booking_id]

    def get_all_bookings(self) -> list:
        """Return all bookings sorted by booking ID."""
        return sorted(self._bookings.values(), key=lambda b: b.booking_id)

    def check_in_guest(self, booking_id: str) -> "Booking":
        """
        Process the check-in for a booking.

        Delegates to Booking.check_in(), which in turn updates the Room's status.

        Raises
        ------
        BookingNotFoundError
        InvalidStateError
        """
        booking = self.get_booking(booking_id)
        booking.check_in()  # Booking.check_in() calls Room.check_in() internally
        save_bookings(list(self._bookings.values()))
        save_rooms(list(self._rooms.values()))
        return booking

    def check_out_guest(self, booking_id: str) -> "Booking":
        """
        Process the check-out for a booking and calculate the final bill.

        Raises
        ------
        BookingNotFoundError
        InvalidStateError
        """
        booking = self.get_booking(booking_id)
        booking.check_out()  # Booking.check_out() calls Room.check_out() internally
        save_bookings(list(self._bookings.values()))
        save_rooms(list(self._rooms.values()))
        return booking

    def cancel_booking(self, booking_id: str) -> "Booking":
        """
        Cancel a booking and free the associated room.

        Raises
        ------
        BookingNotFoundError
        InvalidStateError
        """
        booking = self.get_booking(booking_id)
        booking.cancel()  # Booking.cancel() calls Room.free() internally
        save_bookings(list(self._bookings.values()))
        save_rooms(list(self._rooms.values()))
        return booking

    def get_bookings_for_guest(self, guest_id: str) -> list:
        """
        Return all bookings for a specific guest.

        Raises
        ------
        GuestNotFoundError
        """
        guest = self.get_guest(guest_id)
        return guest.get_booking_history(list(self._bookings.values()))

    def get_bookings_in_range(self, start_date, end_date) -> list:
        """
        Return all bookings that overlap with a date range.

        Parameters
        ----------
        start_date : date
        end_date : date

        Returns
        -------
        list of Booking
        """
        return [
            b for b in self._bookings.values()
            if b.overlaps_with(start_date, end_date)
        ]

    def export_report(self):
        """Generate and save the daily occupancy report to a text file."""
        export_daily_report(
            rooms    = list(self._rooms.values()),
            bookings = list(self._bookings.values()),
        )
