🏨 HotelHub — Hotel Reservations & Guest Management System

A fully-featured hotel management system built in Python, featuring a
command-line interface (CLI) and a Streamlit web GUI. Handles room inventory,
guest registration, booking management, check-in/check-out workflows, and
occupancy reporting.

📁 Project Structure

hotelhub/ ├── exceptions.py # Custom exception hierarchy ├── classes.py # Room,
Guest, Booking OOP classes ├── validation.py # Input validation utilities ├──
file_handling.py # CSV read/write (data persistence) ├── reporting.py # Report
and billing generators ├── hotel_manager.py # Central manager (business logic)
├── main.py # CLI menu-driven interface ├── app.py # Streamlit web GUI ├──
requirements.txt # Python dependencies ├── report.md # Technical design report
├── README.md # This file └── data/ # Auto-created; stores CSV files ├──
rooms.csv ├── guests.csv ├── bookings.csv └── daily_occupancy_report.txt

How to run the code? 

python main.py

python -m streamlit run app.py
