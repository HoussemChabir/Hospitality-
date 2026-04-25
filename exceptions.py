"""
exceptions.py
=============
This module defines ALL custom exceptions used by HotelHub.

WHY a dedicated exceptions file?
---------------------------------
Instead of raising generic Python errors (like plain `Exception`), we create
our own error types that are specific to the hotel domain. This makes it
crystal-clear WHAT went wrong and WHERE — both for the developer reading the
code and for the `except` clauses that catch them.

Think of it like this: a fire alarm (generic) vs. a "Kitchen Fire" alarm
(specific). The specific one tells you exactly what to do next.
"""


# ─────────────────────────────────────────────────────────────
# BASE (PARENT) EXCEPTION
# ─────────────────────────────────────────────────────────────

class HotelHubError(Exception):
    """
    The base class for all HotelHub-specific errors.

    Every custom exception in this project inherits from this class.
    This is useful because you can catch ALL hotel errors with a single
    `except HotelHubError` clause, or catch specific ones individually.

    Parameters
    ----------
    message : str
        A human-readable description of what went wrong.
    """

    def __init__(self, message: str = "An unexpected hotel system error occurred."):
        # Call the parent Exception class to store the message properly
        super().__init__(message)
        # Also save it as an attribute for easy access
        self.message = message

    def __str__(self):
        """Return a clean string when this error is printed."""
        return f"[HotelHub Error] {self.message}"


# ─────────────────────────────────────────────────────────────
# BOOKING-RELATED EXCEPTIONS
# ─────────────────────────────────────────────────────────────

class BookingConflictError(HotelHubError):
    """
    Raised when a new booking overlaps with an existing one for the same room.

    Example scenario: Room 101 is booked Jan 10–15. Someone tries to book it
    for Jan 13–18. The dates conflict, so this error is raised.

    Parameters
    ----------
    room_number : str or int
        The room number that has the conflict.
    conflict_booking_id : str
        The ID of the existing booking that clashes.
    """

    def __init__(self, room_number, conflict_booking_id: str):
        message = (
            f"Room {room_number} is already booked (Booking ID: {conflict_booking_id}) "
            f"for the requested dates. Please choose different dates or another room."
        )
        super().__init__(message)
        # Store extra info so callers can inspect it if needed
        self.room_number = room_number
        self.conflict_booking_id = conflict_booking_id


class InvalidStateError(HotelHubError):
    """
    Raised when an action is attempted on an object that is in the wrong state.

    Example scenarios:
    - Trying to check in a guest to a room that is already occupied.
    - Trying to cancel a booking that is already checked-out or cancelled.
    - Trying to check out a booking that was never checked in.

    Parameters
    ----------
    entity : str
        What entity is in the wrong state (e.g., "Room 101", "Booking BK-001").
    current_state : str
        What state the entity is currently in (e.g., "occupied", "cancelled").
    required_state : str
        What state was required for the action (e.g., "available", "confirmed").
    """

    def __init__(self, entity: str, current_state: str, required_state: str):
        message = (
            f"Cannot perform this action on '{entity}'. "
            f"Current state: '{current_state}'. Required state: '{required_state}'."
        )
        super().__init__(message)
        self.entity = entity
        self.current_state = current_state
        self.required_state = required_state


class BookingNotFoundError(HotelHubError):
    """
    Raised when a booking lookup fails because the ID does not exist.

    Parameters
    ----------
    booking_id : str
        The booking ID that could not be found.
    """

    def __init__(self, booking_id: str):
        message = f"Booking '{booking_id}' was not found in the system."
        super().__init__(message)
        self.booking_id = booking_id


# ─────────────────────────────────────────────────────────────
# GUEST-RELATED EXCEPTIONS
# ─────────────────────────────────────────────────────────────

class GuestNotFoundError(HotelHubError):
    """
    Raised when a guest lookup fails because the ID does not exist.

    Parameters
    ----------
    guest_id : str
        The guest ID that could not be found.
    """

    def __init__(self, guest_id: str):
        message = f"Guest '{guest_id}' was not found in the system."
        super().__init__(message)
        self.guest_id = guest_id


class InvalidEmailError(HotelHubError):
    """
    Raised when an email address fails basic format validation.

    Parameters
    ----------
    email : str
        The invalid email that was provided.
    """

    def __init__(self, email: str):
        message = (
            f"'{email}' is not a valid email address. "
            f"Please use the format: name@domain.com"
        )
        super().__init__(message)
        self.email = email


class InvalidPhoneError(HotelHubError):
    """
    Raised when a phone number fails basic format validation.

    Parameters
    ----------
    phone : str
        The invalid phone number that was provided.
    """

    def __init__(self, phone: str):
        message = (
            f"'{phone}' is not a valid phone number. "
            f"Please enter digits only (8–15 characters)."
        )
        super().__init__(message)
        self.phone = phone


# ─────────────────────────────────────────────────────────────
# ROOM-RELATED EXCEPTIONS
# ─────────────────────────────────────────────────────────────

class RoomNotFoundError(HotelHubError):
    """
    Raised when a room lookup fails because the room number does not exist.

    Parameters
    ----------
    room_number : str or int
        The room number that could not be found.
    """

    def __init__(self, room_number):
        message = f"Room '{room_number}' was not found in the system."
        super().__init__(message)
        self.room_number = room_number


class RoomAlreadyExistsError(HotelHubError):
    """
    Raised when someone tries to add a room with a number that already exists.

    Parameters
    ----------
    room_number : str or int
        The duplicate room number.
    """

    def __init__(self, room_number):
        message = f"Room '{room_number}' already exists. Use a different room number."
        super().__init__(message)
        self.room_number = room_number


# ─────────────────────────────────────────────────────────────
# DATE-RELATED EXCEPTIONS
# ─────────────────────────────────────────────────────────────

class InvalidDateRangeError(HotelHubError):
    """
    Raised when date logic is broken — e.g., check-out is before check-in.

    Parameters
    ----------
    check_in : str
        The check-in date string.
    check_out : str
        The check-out date string.
    reason : str
        A short explanation of why the range is invalid.
    """

    def __init__(self, check_in: str, check_out: str, reason: str = ""):
        message = (
            f"Invalid date range: check-in '{check_in}', check-out '{check_out}'. "
            f"{reason}"
        )
        super().__init__(message)
        self.check_in = check_in
        self.check_out = check_out


# ─────────────────────────────────────────────────────────────
# FILE-RELATED EXCEPTIONS
# ─────────────────────────────────────────────────────────────

class DataLoadError(HotelHubError):
    """
    Raised when a data file cannot be loaded correctly due to bad formatting.

    Parameters
    ----------
    filename : str
        The file that caused the problem.
    detail : str
        Extra context about what was malformed.
    """

    def __init__(self, filename: str, detail: str = ""):
        message = f"Could not load data from '{filename}'. {detail}"
        super().__init__(message)
        self.filename = filename
