"""
validation.py
=============
This module contains PURE VALIDATION functions — functions that check whether
input data meets certain rules and raise errors if not.

WHY a separate validation module?
-----------------------------------
Validation logic is reused in many places:
    - The CLI (main.py) validates user keyboard input.
    - The hotel_manager validates data before creating objects.
    - The Streamlit GUI validates form fields.

By putting all validation in one place, we follow the DRY principle:
"Don't Repeat Yourself." If the email rule changes, we fix it in ONE place.

Note: Basic format validation (regex) for email/phone is also done inside
the Guest class constructor. This module handles higher-level checks:
date ranges, room-type strings, positive numbers, etc.
"""

from datetime import datetime, date
from exceptions import InvalidDateRangeError

# The date format the entire system uses
DATE_FORMAT = "%Y-%m-%d"


def validate_date_string(date_str: str) -> date:
    """
    Parse a date string in YYYY-MM-DD format and return a date object.

    Parameters
    ----------
    date_str : str
        The date string to parse (e.g., "2025-12-25").

    Returns
    -------
    date
        A Python date object.

    Raises
    ------
    ValueError
        If the string doesn't match the expected format.
    """
    date_str = str(date_str).strip()
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(
            f"Date '{date_str}' is not in the correct format. "
            f"Please use YYYY-MM-DD (e.g., 2025-12-25)."
        )


def validate_date_range(check_in_str: str, check_out_str: str):
    """
    Validate a check-in / check-out date range.

    Rules enforced:
    1. Both dates must be parseable as YYYY-MM-DD.
    2. check-out must be strictly AFTER check-in.
    3. check-in must not be in the past (optional, controlled by flag).

    Parameters
    ----------
    check_in_str : str
        Check-in date string.
    check_out_str : str
        Check-out date string.

    Returns
    -------
    tuple (date, date)
        The validated (check_in_date, check_out_date) as date objects.

    Raises
    ------
    ValueError
        If either date string is malformed.
    InvalidDateRangeError
        If the range is logically invalid.
    """
    check_in  = validate_date_string(check_in_str)
    check_out = validate_date_string(check_out_str)

    if check_out <= check_in:
        raise InvalidDateRangeError(
            check_in=check_in_str,
            check_out=check_out_str,
            reason="Check-out must be at least one day after check-in.",
        )

    return check_in, check_out


def validate_positive_number(value, field_name: str = "Value") -> float:
    """
    Ensure a value is a positive number.

    Parameters
    ----------
    value : any
        The value to check (will be cast to float).
    field_name : str
        Name of the field for the error message.

    Returns
    -------
    float
        The validated positive number.

    Raises
    ------
    ValueError
        If the value is not a positive number.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' must be a number. Got: '{value}'.")

    if number <= 0:
        raise ValueError(f"'{field_name}' must be greater than zero. Got: {number}.")

    return number


def validate_non_empty_string(value: str, field_name: str = "Field") -> str:
    """
    Ensure a string is not empty after stripping whitespace.

    Parameters
    ----------
    value : str
        The string to validate.
    field_name : str
        Name of the field for the error message.

    Returns
    -------
    str
        The stripped, non-empty string.

    Raises
    ------
    ValueError
        If the string is empty.
    """
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"'{field_name}' cannot be empty.")
    return cleaned


def validate_room_type(room_type: str) -> str:
    """
    Validate and normalize a room type string.

    Parameters
    ----------
    room_type : str
        The room type to validate.

    Returns
    -------
    str
        The lowercased, validated room type.

    Raises
    ------
    ValueError
        If the room type is not one of the accepted values.
    """
    from classes import VALID_ROOM_TYPES  # local import to avoid circularity
    normalized = room_type.strip().lower()
    if normalized not in VALID_ROOM_TYPES:
        raise ValueError(
            f"Room type '{room_type}' is invalid. "
            f"Choose from: {', '.join(VALID_ROOM_TYPES)}."
        )
    return normalized


def validate_booking_id_format(booking_id: str) -> str:
    """
    Ensure a booking ID follows the BK-XXX pattern.

    Parameters
    ----------
    booking_id : str
        The booking ID string.

    Returns
    -------
    str
        Validated and uppercased booking ID.

    Raises
    ------
    ValueError
        If format is wrong.
    """
    cleaned = str(booking_id).strip().upper()
    if not cleaned.startswith("BK-") or len(cleaned) < 5:
        raise ValueError(
            f"Booking ID '{booking_id}' format is invalid. Expected: BK-XXX."
        )
    return cleaned
