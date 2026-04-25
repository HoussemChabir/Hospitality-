"""
classes.py
==========
This module defines the three core domain classes for HotelHub:

    - Room    → Represents a physical hotel room.
    - Guest   → Represents a registered hotel guest.
    - Booking → Represents a reservation linking a Guest to a Room.

WHY are all three classes in one file?
---------------------------------------
They are tightly related domain objects. Splitting them across three separate
files would require importing between them in complex ways. Keeping them here
prevents circular import issues and keeps domain logic in one readable place.

All business logic lives inside the class methods — NOT in main.py.
This is the core principle of Object-Oriented Programming: data and the
functions that operate on that data belong together.
"""

# We need datetime to handle check-in/check-out date calculations
from datetime import datetime, date

# Import our custom exceptions so classes can raise meaningful errors
from exceptions import (
    InvalidStateError,
    InvalidDateRangeError,
    InvalidEmailError,
    InvalidPhoneError,
)

# Re module is for Regular Expressions — used to validate email/phone format
import re


# ════════════════════════════════════════════════════════════════
# CONSTANTS (module-level values shared by all classes)
# ════════════════════════════════════════════════════════════════

# Valid room types the hotel supports — using a tuple so it's immutable
VALID_ROOM_TYPES = ("single", "double", "suite")

# Date format used throughout the system (YYYY-MM-DD)
DATE_FORMAT = "%Y-%m-%d"

# Valid room statuses
STATUS_AVAILABLE = "available"
STATUS_OCCUPIED  = "occupied"
STATUS_RESERVED  = "reserved"   # booked but guest hasn't arrived yet

# Valid booking statuses
BOOKING_CONFIRMED  = "confirmed"
BOOKING_CHECKED_IN = "checked_in"
BOOKING_CHECKED_OUT = "checked_out"
BOOKING_CANCELLED  = "cancelled"


# ════════════════════════════════════════════════════════════════
# CLASS 1: ROOM
# ════════════════════════════════════════════════════════════════

class Room:
    """
    Represents a single hotel room with its type, price, and availability status.

    Attributes (public)
    -------------------
    room_number : str
        Unique identifier for the room (e.g., "101", "202").
    room_type : str
        Category of the room — one of: 'single', 'double', 'suite'.
    price_per_night : float
        Nightly rate charged to guests.

    Attributes (private/encapsulated)
    -----------------------------------
    _status : str
        Current room state. Private so it can only be changed through
        the safe methods check_in() and check_out(), preventing
        accidental or invalid status changes from outside the class.
    """

    def __init__(self, room_number: str, room_type: str, price_per_night: float):
        """
        Create a new Room instance.

        Parameters
        ----------
        room_number : str
            The room's unique number (e.g., "101").
        room_type : str
            Must be 'single', 'double', or 'suite'.
        price_per_night : float
            The nightly cost. Must be a positive number.

        Raises
        ------
        ValueError
            If room_type is not valid or price is not positive.
        """
        # ── Validate room_type before storing it ──
        # We lowercase it so "Double" and "double" are treated the same
        room_type = room_type.strip().lower()
        if room_type not in VALID_ROOM_TYPES:
            raise ValueError(
                f"Invalid room type '{room_type}'. "
                f"Choose from: {VALID_ROOM_TYPES}"
            )

        # ── Validate price ──
        if price_per_night <= 0:
            raise ValueError("Price per night must be a positive number.")

        # ── Store validated attributes ──
        self.room_number     = str(room_number).strip()
        self.room_type       = room_type
        self.price_per_night = float(price_per_night)

        # _status is PRIVATE (note the underscore prefix).
        # WHY? We want all status changes to go through check_in() and
        # check_out() so we can enforce rules (e.g., can't check in if
        # already occupied). If _status were public, any code could
        # set room._status = "occupied" without any safety checks.
        self._status = STATUS_AVAILABLE  # Every new room starts available

    # ── Property: read-only access to the private status ──
    @property
    def status(self) -> str:
        """
        Read-only property to view the room's current status.
        Using @property lets callers write `room.status` (not `room._status`)
        while still keeping the attribute protected from direct assignment.
        """
        return self._status

    # ── METHODS ──

    def is_available(self) -> bool:
        """
        Check whether the room can accept a new booking.

        Returns
        -------
        bool
            True if the room status is 'available', False otherwise.
        """
        return self._status == STATUS_AVAILABLE

    def check_in(self):
        """
        Mark the room as occupied when a guest arrives.

        This is a GUARD CLAUSE pattern: we check pre-conditions first and
        raise an error if the action isn't valid, rather than letting silent
        data corruption happen.

        Raises
        ------
        InvalidStateError
            If the room is not in 'available' or 'reserved' state.
        """
        # Guard clause: only allow check-in from valid states
        if self._status not in (STATUS_AVAILABLE, STATUS_RESERVED):
            raise InvalidStateError(
                entity=f"Room {self.room_number}",
                current_state=self._status,
                required_state="available or reserved",
            )
        # Safe to proceed — change the status
        self._status = STATUS_OCCUPIED

    def check_out(self):
        """
        Mark the room as available again after a guest departs.

        Raises
        ------
        InvalidStateError
            If the room is not currently occupied.
        """
        # Guard clause: can only check out an occupied room
        if self._status != STATUS_OCCUPIED:
            raise InvalidStateError(
                entity=f"Room {self.room_number}",
                current_state=self._status,
                required_state="occupied",
            )
        # Reset to available for the next guest
        self._status = STATUS_AVAILABLE

    def reserve(self):
        """
        Mark the room as reserved (booked but guest not yet arrived).

        Raises
        ------
        InvalidStateError
            If the room is not currently available.
        """
        if self._status != STATUS_AVAILABLE:
            raise InvalidStateError(
                entity=f"Room {self.room_number}",
                current_state=self._status,
                required_state="available",
            )
        self._status = STATUS_RESERVED

    def free(self):
        """
        Return the room to 'available' status (used when a booking is cancelled).
        Works from either 'reserved' or 'occupied' state.
        """
        self._status = STATUS_AVAILABLE

    def get_info(self) -> dict:
        """
        Return a dictionary snapshot of all room information.

        WHY return a dict?
        ------------------
        Dictionaries are easy to display, convert to CSV rows, or pass to
        a GUI framework. It's a clean, neutral data format.

        Returns
        -------
        dict
            Keys: room_number, room_type, price_per_night, status.
        """
        return {
            "room_number":     self.room_number,
            "room_type":       self.room_type,
            "price_per_night": self.price_per_night,
            "status":          self._status,
        }

    def __repr__(self) -> str:
        """Developer-friendly string representation (shown in debugger/REPL)."""
        return (
            f"Room(number={self.room_number!r}, type={self.room_type!r}, "
            f"price={self.price_per_night:.2f}, status={self._status!r})"
        )

    def __str__(self) -> str:
        """User-friendly string representation (shown when you print a Room)."""
        return (
            f"Room {self.room_number} | {self.room_type.title()} | "
            f"${self.price_per_night:.2f}/night | Status: {self._status.upper()}"
        )


# ════════════════════════════════════════════════════════════════
# CLASS 2: GUEST
# ════════════════════════════════════════════════════════════════

class Guest:
    """
    Represents a hotel guest with their personal and contact details.

    Attributes
    ----------
    guest_id : str
        Unique identifier for the guest (e.g., "G-001").
    full_name : str
        The guest's full name.
    email : str
        Contact email address (validated on creation).
    phone : str
        Contact phone number (validated on creation).
    id_number : str
        Government-issued ID or passport number.
    """

    # Email pattern: something@something.something
    _EMAIL_PATTERN = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")

    # Phone pattern: digits only, 8–15 characters
    _PHONE_PATTERN = re.compile(r"^\d{8,15}$")

    def __init__(
        self,
        guest_id: str,
        full_name: str,
        email: str,
        phone: str,
        id_number: str,
    ):
        """
        Create a new Guest instance with validated contact information.

        Parameters
        ----------
        guest_id : str
            Unique ID (e.g., "G-001").
        full_name : str
            Guest's full name.
        email : str
            Must follow standard email format.
        phone : str
            Must be 8–15 digits.
        id_number : str
            Passport or national ID number.

        Raises
        ------
        InvalidEmailError
            If the email format is invalid.
        InvalidPhoneError
            If the phone number format is invalid.
        ValueError
            If name or id_number are empty.
        """
        # ── Validate name ──
        full_name = full_name.strip()
        if not full_name:
            raise ValueError("Guest full name cannot be empty.")

        # ── Validate email using the regex pattern ──
        email = email.strip()
        if not self._EMAIL_PATTERN.match(email):
            raise InvalidEmailError(email)

        # ── Validate phone ──
        # Remove common separators first so "012-345-6789" still works
        phone_digits = re.sub(r"[\s\-\+\(\)]", "", phone)
        if not self._PHONE_PATTERN.match(phone_digits):
            raise InvalidPhoneError(phone)

        # ── Validate id_number ──
        id_number = id_number.strip()
        if not id_number:
            raise ValueError("Guest ID number cannot be empty.")

        # ── Store validated attributes ──
        self.guest_id  = str(guest_id).strip()
        self.full_name = full_name
        self.email     = email
        self.phone     = phone_digits   # store cleaned digits
        self.id_number = id_number

    def to_dict(self) -> dict:
        """
        Serialize the guest to a plain dictionary.

        WHY to_dict()?
        --------------
        This is used when saving guest data to a CSV file. The file_handling
        module will call guest.to_dict() and write those key-value pairs as
        a CSV row. It keeps the serialization logic inside the class.

        Returns
        -------
        dict
            All guest attributes as a flat dictionary.
        """
        return {
            "guest_id":  self.guest_id,
            "full_name": self.full_name,
            "email":     self.email,
            "phone":     self.phone,
            "id_number": self.id_number,
        }

    def get_booking_history(self, all_bookings: list) -> list:
        """
        Find all bookings associated with this guest.

        Parameters
        ----------
        all_bookings : list of Booking
            The full list of bookings from the hotel manager.

        Returns
        -------
        list of Booking
            Only the bookings that belong to this guest.

        Note
        ----
        We pass in all_bookings from outside because the Guest class doesn't
        own or store bookings directly. This avoids circular references and
        keeps the class design simple.
        """
        return [b for b in all_bookings if b.guest.guest_id == self.guest_id]

    def __repr__(self) -> str:
        return f"Guest(id={self.guest_id!r}, name={self.full_name!r})"

    def __str__(self) -> str:
        return (
            f"Guest [{self.guest_id}] | {self.full_name} | "
            f"{self.email} | Phone: {self.phone}"
        )


# ════════════════════════════════════════════════════════════════
# CLASS 3: BOOKING
# ════════════════════════════════════════════════════════════════

class Booking:
    """
    Represents a hotel reservation linking a Guest to a Room for a date range.

    This is the most complex class because it ties everything together and
    contains the most business logic (date math, total calculation, lifecycle).

    Attributes (public)
    -------------------
    booking_id : str
        Unique reservation ID (e.g., "BK-001").
    guest : Guest
        The Guest object making the booking. Stored as an object, not just an
        ID, so we can access guest details directly (guest.full_name, etc.).
    room : Room
        The Room object being reserved.
    check_in_date : date
        The date the guest arrives.
    check_out_date : date
        The date the guest departs.

    Attributes (private)
    --------------------
    _status : str
        The booking's lifecycle state. Private for the same reason as Room._status.
    """

    def __init__(
        self,
        booking_id: str,
        guest: "Guest",
        room: "Room",
        check_in_date,
        check_out_date,
    ):
        """
        Create a new Booking instance.

        Parameters
        ----------
        booking_id : str
            Unique ID for this booking (e.g., "BK-001").
        guest : Guest
            The Guest object associated with this booking.
        room : Room
            The Room object being reserved.
        check_in_date : str or date
            Check-in date. If a string, it must be in YYYY-MM-DD format.
        check_out_date : str or date
            Check-out date. Must be after check_in_date.

        Raises
        ------
        InvalidDateRangeError
            If check-out is not after check-in.
        ValueError
            If date strings cannot be parsed.
        """
        self.booking_id = str(booking_id).strip()
        self.guest      = guest   # Store the FULL Guest object (delegation)
        self.room       = room    # Store the FULL Room object (delegation)

        # ── Parse and validate dates ──
        # We accept both string and date objects for flexibility
        self.check_in_date  = self._parse_date(check_in_date)
        self.check_out_date = self._parse_date(check_out_date)

        # Guard clause: check-out must be AFTER check-in
        if self.check_out_date <= self.check_in_date:
            raise InvalidDateRangeError(
                check_in=str(self.check_in_date),
                check_out=str(self.check_out_date),
                reason="Check-out date must be after check-in date.",
            )

        # All new bookings start as 'confirmed' (guest has a reservation but
        # hasn't arrived yet)
        self._status = BOOKING_CONFIRMED

    # ── STATIC HELPER: parse date strings ──

    @staticmethod
    def _parse_date(value) -> date:
        """
        Convert a value to a date object.

        WHY static method?
        ------------------
        This helper doesn't need access to `self` or `cls`. Making it
        @staticmethod signals to the reader: "this is a pure utility function
        that just converts data — it has no side effects."

        Parameters
        ----------
        value : str or date or datetime
            The value to parse.

        Returns
        -------
        date
            A Python date object.

        Raises
        ------
        ValueError
            If the string cannot be parsed as YYYY-MM-DD.
        """
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        # It's a string — try to parse it
        try:
            return datetime.strptime(str(value).strip(), DATE_FORMAT).date()
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{value}'. Expected YYYY-MM-DD."
            )

    # ── Property: read-only access to the private status ──

    @property
    def status(self) -> str:
        """Read-only view of the booking's current lifecycle status."""
        return self._status

    # ── METHODS ──

    def duration_nights(self) -> int:
        """
        Calculate how many nights the guest is staying.

        Returns
        -------
        int
            Number of nights between check-in and check-out.
        """
        delta = self.check_out_date - self.check_in_date
        return delta.days  # .days gives the difference as an integer

    def calculate_total(self) -> float:
        """
        Calculate the total cost of this booking.

        Formula: price_per_night × number_of_nights

        Returns
        -------
        float
            Total amount owed by the guest.
        """
        return self.room.price_per_night * self.duration_nights()

    def confirm(self):
        """
        Confirm the booking (e.g., after payment is received).
        Transition: any non-cancelled state → confirmed.

        Raises
        ------
        InvalidStateError
            If the booking is already cancelled or checked-out.
        """
        if self._status in (BOOKING_CANCELLED, BOOKING_CHECKED_OUT):
            raise InvalidStateError(
                entity=f"Booking {self.booking_id}",
                current_state=self._status,
                required_state="not cancelled or checked-out",
            )
        self._status = BOOKING_CONFIRMED

    def check_in(self):
        """
        Mark the booking as checked-in (guest has arrived at the hotel).

        Also calls room.check_in() so the room status is updated automatically.
        This is DELEGATION in action: Booking tells Room to update itself.

        Raises
        ------
        InvalidStateError
            If the booking is not in 'confirmed' state.
        """
        # Guard: can only check in a confirmed booking
        if self._status != BOOKING_CONFIRMED:
            raise InvalidStateError(
                entity=f"Booking {self.booking_id}",
                current_state=self._status,
                required_state=BOOKING_CONFIRMED,
            )
        # Update booking status first
        self._status = BOOKING_CHECKED_IN
        # Then delegate room status change to the Room object
        self.room.check_in()

    def check_out(self):
        """
        Mark the booking as checked-out (guest has departed).

        Also frees the room so it's available for new bookings.

        Raises
        ------
        InvalidStateError
            If the booking is not in 'checked_in' state.
        """
        if self._status != BOOKING_CHECKED_IN:
            raise InvalidStateError(
                entity=f"Booking {self.booking_id}",
                current_state=self._status,
                required_state=BOOKING_CHECKED_IN,
            )
        self._status = BOOKING_CHECKED_OUT
        # Delegate: tell the room it's free again
        self.room.check_out()

    def cancel(self):
        """
        Cancel the booking.

        You can cancel a booking that is 'confirmed' or 'checked_in'.
        You CANNOT cancel one that is already 'checked_out' or 'cancelled'.

        Raises
        ------
        InvalidStateError
            If the booking has already ended or been cancelled.
        """
        # Guard: cannot cancel a completed or already-cancelled booking
        if self._status in (BOOKING_CHECKED_OUT, BOOKING_CANCELLED):
            raise InvalidStateError(
                entity=f"Booking {self.booking_id}",
                current_state=self._status,
                required_state="confirmed or checked_in",
            )
        self._status = BOOKING_CANCELLED
        # Free the room so it's available for other guests
        self.room.free()

    def overlaps_with(self, other_check_in: date, other_check_out: date) -> bool:
        """
        Check whether this booking's date range overlaps with another range.

        WHY is this logic inside Booking?
        -----------------------------------
        The Booking object owns its own date range, so it's the right place
        to answer questions about that date range. Putting this in a standalone
        function elsewhere would break encapsulation.

        Overlap occurs when:
            existing_check_in  < new_check_out
            AND
            existing_check_out > new_check_in

        Parameters
        ----------
        other_check_in : date
            The proposed new booking's check-in date.
        other_check_out : date
            The proposed new booking's check-out date.

        Returns
        -------
        bool
            True if there is an overlap, False otherwise.
        """
        # A cancelled or checked-out booking doesn't block new reservations
        if self._status in (BOOKING_CANCELLED, BOOKING_CHECKED_OUT):
            return False

        # Standard interval overlap formula
        return (
            self.check_in_date < other_check_out
            and self.check_out_date > other_check_in
        )

    def to_dict(self) -> dict:
        """
        Serialize the booking to a flat dictionary for CSV saving.

        Returns
        -------
        dict
            All booking data with primitive (non-object) values.
        """
        return {
            "booking_id":     self.booking_id,
            "guest_id":       self.guest.guest_id,
            "room_number":    self.room.room_number,
            "check_in_date":  str(self.check_in_date),
            "check_out_date": str(self.check_out_date),
            "status":         self._status,
            "total_cost":     round(self.calculate_total(), 2),
        }

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.booking_id!r}, guest={self.guest.full_name!r}, "
            f"room={self.room.room_number!r}, status={self._status!r})"
        )

    def __str__(self) -> str:
        return (
            f"Booking [{self.booking_id}] | Guest: {self.guest.full_name} | "
            f"Room: {self.room.room_number} ({self.room.room_type}) | "
            f"{self.check_in_date} → {self.check_out_date} | "
            f"{self.duration_nights()} nights | "
            f"Total: ${self.calculate_total():.2f} | Status: {self._status.upper()}"
        )
