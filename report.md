# HotelHub — Technical Design Report

**Project:** HotelHub: Hotel Reservations & Guest Management System  
**Author:** Student Submission  
**Word Count:** ~650

---

## 1. Class Design Rationale

The system is built around three domain classes — `Room`, `Guest`, and `Booking` — each modelling a real-world entity with attributes and behaviour that belong naturally to it.

**Room** encapsulates a physical hotel room. Its most important design decision is the *private* `_status` attribute. Rather than allowing external code to freely set `room._status = "occupied"`, access is controlled through the `check_in()`, `check_out()`, `reserve()`, and `free()` methods. Each of these applies a **guard clause** — checking the current state before allowing the transition — so that an already-occupied room can never be checked in twice. This is *encapsulation* in practice: the class protects its own data integrity.

**Guest** owns its contact data and includes validation on construction. Email is checked against a regular-expression pattern and phone digits are cleaned and length-validated before storage. This means the rest of the system can trust that any `Guest` object already has valid contact information — no downstream re-validation is needed. The `to_dict()` method handles serialisation for CSV export, keeping that logic inside the class rather than scattering it across file-handling code.

**Booking** is the most complex class because it bridges the other two. It stores full `Guest` and `Room` *objects* (not just their IDs), enabling direct attribute access (`booking.guest.full_name`) without additional lookups. The `calculate_total()` method delegates the price lookup to `booking.room.price_per_night`, demonstrating *delegation*: Booking asks Room for the data it needs rather than duplicating it. The `overlaps_with()` method encapsulates date-conflict logic directly on the entity that owns the date range, keeping collision detection clean and testable. The `_status` attribute is again private, with lifecycle transitions enforced through `confirm()`, `check_in()`, `check_out()`, and `cancel()`.

---

## 2. Module Structure Rationale

The project follows the **Single Responsibility Principle** — each file has exactly one reason to exist:

| File | Responsibility |
|---|---|
| `exceptions.py` | Domain exception hierarchy only |
| `classes.py` | Room, Guest, Booking class definitions |
| `validation.py` | Pure input validation utilities |
| `file_handling.py` | All CSV read/write operations |
| `reporting.py` | Read-only report and summary generation |
| `hotel_manager.py` | Cross-entity coordination and state management |
| `main.py` | CLI menu display and user input only |
| `app.py` | Streamlit GUI only |

This separation produces two major benefits. First, **zero circular imports**: each module only imports from lower layers (e.g., `hotel_manager` imports from `classes`, `file_handling`, and `exceptions`, but none of those import back). Second, **swappable components**: replacing CSV storage with a database only requires editing `file_handling.py` — the manager, classes, and interfaces are untouched.

`main.py` deliberately contains no business logic. Every menu handler collects input, calls a `HotelManager` method, and prints the result. This makes the CLI a thin *orchestrator*, not a decision-maker.

---

## 3. Exception Strategy

A dedicated `exceptions.py` defines a hierarchy rooted at `HotelHubError`. Specific subclasses — `BookingConflictError`, `InvalidStateError`, `GuestNotFoundError`, `RoomNotFoundError`, `InvalidEmailError`, `InvalidDateRangeError`, and others — carry precise context (the offending ID, state, or value) as attributes, making them informative for both the user message and any programmatic handling.

**Prevention** is handled at the class constructor level: `Room` rejects invalid types and negative prices, `Guest` validates email and phone on creation, and `Booking` enforces that check-out follows check-in. Errors caught this early never propagate into business logic.

**Recovery** is handled at the boundary between the system and the outside world. In `file_handling.py`, every file operation is wrapped in `try-except OSError` and `try-except DataLoadError`. A missing or malformed CSV triggers a warning and an empty-list fallback — the system starts fresh rather than crashing. In `main.py` and `app.py`, every user-triggered action is wrapped in `try-except HotelHubError` (catching all domain errors in one clause) plus `try-except ValueError` (catching bad number/date input). The program **never crashes** on bad user input; it displays a polite error and returns to the menu.

This layered strategy — prevent at construction, recover at I/O boundaries, report at the user interface — ensures that errors are caught at the layer best equipped to handle them, producing a robust and user-friendly application.
