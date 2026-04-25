"""
app.py
======
The Streamlit Graphical User Interface (GUI) for HotelHub.

HOW TO RUN:
    streamlit run app.py

WHY a separate GUI file?
--------------------------
The GUI is completely separate from the CLI (main.py). Both import the same
HotelManager backend, but they present it differently. This means:
  - The backend logic never changes based on how the user accesses it.
  - We can add a web interface without touching any business logic.
  - If Streamlit is not installed, the CLI still works fine.

HOW Streamlit works (beginner note):
--------------------------------------
Streamlit re-runs the entire script from top to bottom every time a user
interacts with any widget. To preserve state between re-runs, we use
`st.session_state`, which is a dictionary that persists across runs.
"""

import streamlit as st
import pandas as pd

# Import our backend
from hotel_manager import HotelManager
from reporting import generate_billing_summary, get_room_type_stats
from exceptions import HotelHubError
from validation import validate_date_range, validate_positive_number

# ── Streamlit page configuration (must be the FIRST Streamlit command) ──
st.set_page_config(
    page_title  = "HotelHub",
    page_icon   = "🏨",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ════════════════════════════════════════════════════════════════
# SESSION STATE: Initialise the HotelManager once per session
# ════════════════════════════════════════════════════════════════

# WHY session_state?
# ------------------
# Streamlit re-runs the script on every user interaction.
# Without session_state, we'd create a new HotelManager every time,
# losing all in-memory changes. session_state persists for the browser tab.

if "manager" not in st.session_state:
    st.session_state.manager = HotelManager()

# Shortcut reference — makes the code below less verbose
manager: HotelManager = st.session_state.manager


# ════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/color/96/hotel.png", width=80)
    st.title("🏨 HotelHub")
    st.caption("Hotel Reservations & Guest Management")
    st.divider()

    page = st.radio(
        "Navigate to:",
        options=[
            "📊 Dashboard",
            "🛏️ Room Management",
            "👤 Guest Management",
            "📋 Booking Management",
            "📈 Reports",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("HotelHub v1.0 — Built with Streamlit")


# ════════════════════════════════════════════════════════════════
# PAGE 1: DASHBOARD
# ════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.title("📊 Hotel Dashboard")
    st.caption("Live overview of current hotel status")

    rooms    = manager.get_all_rooms()
    guests   = manager.get_all_guests()
    bookings = manager.get_all_bookings()

    # ── KPI Cards (Key Performance Indicators) ──
    col1, col2, col3, col4 = st.columns(4)

    total_rooms     = len(rooms)
    available_rooms = len([r for r in rooms if r.status == "available"])
    occupied_rooms  = len([r for r in rooms if r.status == "occupied"])
    reserved_rooms  = len([r for r in rooms if r.status == "reserved"])
    active_bookings = len([b for b in bookings if b.status in ("confirmed", "checked_in")])

    with col1:
        st.metric("🏨 Total Rooms", total_rooms)
    with col2:
        st.metric("✅ Available", available_rooms)
    with col3:
        st.metric("🔴 Occupied", occupied_rooms)
    with col4:
        st.metric("👤 Registered Guests", len(guests))

    st.divider()

    # ── Charts Row ──
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Room Status Overview")
        if rooms:
            # Build data for the pie chart
            status_data = {
                "Status": ["Available", "Occupied", "Reserved"],
                "Count":  [available_rooms, occupied_rooms, reserved_rooms],
            }
            df_status = pd.DataFrame(status_data).set_index("Status")
            # Show only non-zero slices
            df_status = df_status[df_status["Count"] > 0]
            st.bar_chart(df_status)
        else:
            st.info("No rooms in the system yet. Add rooms to see the chart.")

    with chart_col2:
        st.subheader("Room Type Distribution")
        if rooms:
            stats = get_room_type_stats(rooms)
            type_data = {
                "Room Type": list(stats.keys()),
                "Total":     [v["total"] for v in stats.values()],
                "Occupied":  [v["occupied"] for v in stats.values()],
                "Available": [v["available"] for v in stats.values()],
            }
            df_types = pd.DataFrame(type_data).set_index("Room Type")
            st.bar_chart(df_types[["Available", "Occupied"]])
        else:
            st.info("No room type data available.")

    st.divider()

    # ── Room Grid ──
    st.subheader("🗺️ Room Grid (Visual Availability)")
    if rooms:
        room_cols = st.columns(min(6, len(rooms)))
        color_map = {
            "available": "🟢",
            "occupied":  "🔴",
            "reserved":  "🟡",
        }
        for i, room in enumerate(rooms):
            col_idx = i % len(room_cols)
            with room_cols[col_idx]:
                icon = color_map.get(room.status, "⬜")
                st.markdown(
                    f"""
                    <div style="border:1px solid #ccc; border-radius:8px;
                                padding:10px; text-align:center; margin:4px;
                                background:#f9f9f9;">
                        <b>{icon} {room.room_number}</b><br>
                        <small>{room.room_type.title()}</small><br>
                        <small>${room.price_per_night:.0f}/night</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No rooms added yet.")

    # ── Recent Bookings ──
    st.divider()
    st.subheader("📋 Recent Bookings")
    if bookings:
        booking_data = [b.to_dict() for b in bookings[-10:]]  # Last 10
        df_bookings  = pd.DataFrame(booking_data)
        st.dataframe(df_bookings, use_container_width=True)
    else:
        st.info("No bookings in the system yet.")


# ════════════════════════════════════════════════════════════════
# PAGE 2: ROOM MANAGEMENT
# ════════════════════════════════════════════════════════════════

elif page == "🛏️ Room Management":
    st.title("🛏️ Room Management")

    tab1, tab2 = st.tabs(["Add Room", "View All Rooms"])

    with tab1:
        st.subheader("Add a New Room")
        with st.form("add_room_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                room_number = st.text_input("Room Number", placeholder="e.g., 101")
            with col2:
                room_type = st.selectbox("Room Type", ["single", "double", "suite"])
            with col3:
                price = st.number_input(
                    "Price per Night ($)", min_value=1.0, value=100.0, step=10.0
                )

            submitted = st.form_submit_button("➕ Add Room", use_container_width=True)

        if submitted:
            if not room_number.strip():
                st.error("Room number cannot be empty.")
            else:
                try:
                    room = manager.add_room(room_number.strip(), room_type, price)
                    st.success(f"✅ Room {room.room_number} ({room.room_type}) added at ${room.price_per_night:.2f}/night!")
                    st.rerun()
                except HotelHubError as e:
                    st.error(str(e))
                except ValueError as e:
                    st.error(f"Invalid input: {e}")

    with tab2:
        st.subheader("All Rooms")
        rooms = manager.get_all_rooms()
        if not rooms:
            st.info("No rooms in the system. Use the 'Add Room' tab to add one.")
        else:
            df = pd.DataFrame([r.get_info() for r in rooms])
            df.columns = ["Room #", "Type", "Price/Night ($)", "Status"]
            # Color-code the status column
            def color_status(val):
                colors = {
                    "available": "background-color: #d4edda; color: #155724",
                    "occupied":  "background-color: #f8d7da; color: #721c24",
                    "reserved":  "background-color: #fff3cd; color: #856404",
                }
                return colors.get(val, "")

            styled = df.style.map(color_status, subset=["Status"])
            st.dataframe(styled, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# PAGE 3: GUEST MANAGEMENT
# ════════════════════════════════════════════════════════════════

elif page == "👤 Guest Management":
    st.title("👤 Guest Management")

    tab1, tab2 = st.tabs(["Register Guest", "View All Guests"])

    with tab1:
        st.subheader("Register a New Guest")
        with st.form("register_guest_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name", placeholder="e.g., John Doe")
                email     = st.text_input("Email Address", placeholder="john@example.com")
            with col2:
                phone     = st.text_input("Phone Number (digits only)", placeholder="e.g., 21234567")
                id_number = st.text_input("ID / Passport Number", placeholder="e.g., TN123456")

            submitted = st.form_submit_button("👤 Register Guest", use_container_width=True)

        if submitted:
            try:
                guest = manager.register_guest(full_name, email, phone, id_number)
                st.success(f"✅ Guest registered! ID: **{guest.guest_id}** — {guest.full_name}")
                st.info(f"Save this Guest ID for creating bookings: **{guest.guest_id}**")
                st.rerun()
            except HotelHubError as e:
                st.error(str(e))
            except ValueError as e:
                st.error(f"Invalid input: {e}")

    with tab2:
        st.subheader("All Registered Guests")

        # Search box
        search = st.text_input("🔍 Search by name", placeholder="Type a name to filter...")

        guests = manager.get_all_guests()
        if search:
            guests = [g for g in guests if search.lower() in g.full_name.lower()]

        if not guests:
            st.info("No guests found.")
        else:
            df = pd.DataFrame([g.to_dict() for g in guests])
            df.columns = ["Guest ID", "Full Name", "Email", "Phone", "ID Number"]
            st.dataframe(df, use_container_width=True)

            # Guest history expander
            st.divider()
            st.subheader("Booking History Lookup")
            all_guests = manager.get_all_guests()
            guest_options = {f"{g.guest_id} — {g.full_name}": g for g in all_guests}
            selected_label = st.selectbox("Select a guest", list(guest_options.keys()))
            if selected_label:
                selected_guest = guest_options[selected_label]
                history = manager.get_bookings_for_guest(selected_guest.guest_id)
                if history:
                    df_hist = pd.DataFrame([b.to_dict() for b in history])
                    st.dataframe(df_hist, use_container_width=True)
                    total = sum(b.calculate_total() for b in history)
                    st.metric("Total Spent", f"${total:.2f}")
                else:
                    st.info("This guest has no bookings yet.")


# ════════════════════════════════════════════════════════════════
# PAGE 4: BOOKING MANAGEMENT
# ════════════════════════════════════════════════════════════════

elif page == "📋 Booking Management":
    st.title("📋 Booking Management")

    tab1, tab2, tab3 = st.tabs(["Create Booking", "Manage Bookings", "View All"])

    # ── Tab 1: Create Booking ──
    with tab1:
        st.subheader("Create a New Booking")

        guests = manager.get_all_guests()
        rooms  = manager.get_available_rooms()

        if not guests:
            st.warning("No guests registered. Please register a guest first.")
        elif not rooms:
            st.warning("No available rooms. All rooms are occupied or reserved.")
        else:
            guest_options = {f"{g.guest_id} — {g.full_name}": g.guest_id for g in guests}
            room_options  = {
                f"Room {r.room_number} ({r.room_type}) — ${r.price_per_night:.2f}/night": r.room_number
                for r in rooms
            }

            with st.form("create_booking_form"):
                selected_guest = st.selectbox("Select Guest", list(guest_options.keys()))
                selected_room  = st.selectbox("Select Room", list(room_options.keys()))

                col1, col2 = st.columns(2)
                with col1:
                    check_in = st.date_input("Check-in Date")
                with col2:
                    check_out = st.date_input("Check-out Date")

                submitted = st.form_submit_button("📋 Create Booking", use_container_width=True)

            if submitted:
                try:
                    guest_id    = guest_options[selected_guest]
                    room_number = room_options[selected_room]

                    booking = manager.create_booking(
                        guest_id       = guest_id,
                        room_number    = room_number,
                        check_in_date  = check_in,
                        check_out_date = check_out,
                    )
                    st.success(f"✅ Booking **{booking.booking_id}** created!")
                    st.info(generate_billing_summary(booking))
                    st.rerun()
                except HotelHubError as e:
                    st.error(str(e))
                except ValueError as e:
                    st.error(f"Invalid input: {e}")

    # ── Tab 2: Manage Bookings (check-in, check-out, cancel) ──
    with tab2:
        st.subheader("Manage an Existing Booking")
        booking_id_input = st.text_input("Enter Booking ID (e.g., BK-001)")

        if booking_id_input:
            try:
                booking = manager.get_booking(booking_id_input.strip())
                st.markdown(f"**Booking Found:**")
                st.code(str(booking))

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Check In", use_container_width=True):
                        try:
                            manager.check_in_guest(booking.booking_id)
                            st.success(f"Guest checked in to Room {booking.room.room_number}!")
                            st.rerun()
                        except HotelHubError as e:
                            st.error(str(e))
                with col2:
                    if st.button("🚪 Check Out", use_container_width=True):
                        try:
                            b = manager.check_out_guest(booking.booking_id)
                            st.success(f"Guest checked out! Total: ${b.calculate_total():.2f}")
                            st.info(generate_billing_summary(b))
                            st.rerun()
                        except HotelHubError as e:
                            st.error(str(e))
                with col3:
                    if st.button("❌ Cancel", use_container_width=True):
                        try:
                            manager.cancel_booking(booking.booking_id)
                            st.success("Booking cancelled. Room is now available.")
                            st.rerun()
                        except HotelHubError as e:
                            st.error(str(e))

            except HotelHubError as e:
                st.error(str(e))

    # ── Tab 3: View All Bookings ──
    with tab3:
        st.subheader("All Bookings")
        bookings = manager.get_all_bookings()
        if not bookings:
            st.info("No bookings yet.")
        else:
            # Status filter
            status_filter = st.multiselect(
                "Filter by status",
                ["confirmed", "checked_in", "checked_out", "cancelled"],
                default=["confirmed", "checked_in"],
            )
            filtered = [b for b in bookings if b.status in status_filter]
            if filtered:
                df = pd.DataFrame([b.to_dict() for b in filtered])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No bookings match the selected filters.")


# ════════════════════════════════════════════════════════════════
# PAGE 5: REPORTS
# ════════════════════════════════════════════════════════════════

elif page == "📈 Reports":
    st.title("📈 Reports & Analytics")

    rooms    = manager.get_all_rooms()
    bookings = manager.get_all_bookings()

    col1, col2 = st.columns(2)

    # ── Occupancy Pie Chart ──
    with col1:
        st.subheader("Occupancy by Room Type")
        if rooms:
            stats = get_room_type_stats(rooms)
            chart_data = {
                "Room Type": [],
                "Occupied %": [],
            }
            for rt, data in stats.items():
                if data["total"] > 0:
                    pct = (data["occupied"] / data["total"]) * 100
                    chart_data["Room Type"].append(rt.title())
                    chart_data["Occupied %"].append(round(pct, 1))

            df_pct = pd.DataFrame(chart_data).set_index("Room Type")
            st.bar_chart(df_pct)
        else:
            st.info("No room data available.")

    # ── Revenue Estimate ──
    with col2:
        st.subheader("Revenue Summary")
        completed = [b for b in bookings if b.status == "checked_out"]
        active    = [b for b in bookings if b.status in ("confirmed", "checked_in")]

        total_earned    = sum(b.calculate_total() for b in completed)
        total_projected = sum(b.calculate_total() for b in active)

        st.metric("💰 Total Earned (Checked-out)", f"${total_earned:,.2f}")
        st.metric("📅 Projected Revenue (Active)", f"${total_projected:,.2f}")
        st.metric("📊 Total Bookings", len(bookings))

    st.divider()

    # ── Bookings by Date Range ──
    st.subheader("Bookings in a Date Range")
    col_a, col_b = st.columns(2)
    with col_a:
        range_start = st.date_input("From date", key="rpt_start")
    with col_b:
        range_end   = st.date_input("To date",   key="rpt_end")

    if st.button("🔍 Search Bookings"):
        if range_end <= range_start:
            st.error("End date must be after start date.")
        else:
            results = manager.get_bookings_in_range(range_start, range_end)
            if results:
                df_range = pd.DataFrame([b.to_dict() for b in results])
                st.dataframe(df_range, use_container_width=True)
                st.caption(f"Found {len(results)} booking(s) in this range.")
            else:
                st.info("No bookings found in this date range.")

    st.divider()

    # ── Export Button ──
    st.subheader("Export Daily Report")
    if st.button("📥 Export Report to File"):
        manager.export_report()
        st.success("✅ Report exported to `data/daily_occupancy_report.txt`!")
