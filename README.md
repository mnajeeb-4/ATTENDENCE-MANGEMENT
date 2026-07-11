# University Attendance Management System (AMS) - Streamlit

A comprehensive, production-grade Attendance Management System built with Python and Streamlit. Designed for university environments, it supports separate application modules for Students and Teachers, Role-Based Access Control (RBAC), simulated QR/digital check-ins, offline mode with local caching, and an enterprise-grade attendance matrix dashboard.

## 🚀 Features

*   **Secure Authentication & RBAC:** Uses `st.session_state` with SHA-256 password hashing. Strict role separation: Teachers see global metrics, Students see only their own data.
*   **Student Application:**
    *   **Simulated QR/Digital Check-In:** One-click attendance marking with duplicate prevention.
    *   **Offline Resiliency:** Toggle offline mode to cache attendance records locally. Data automatically syncs to the database when back online.
    *   **Personal Analytics:** View attendance trends, pie charts, and percentage metrics using Plotly.
*   **Teacher Application:**
    *   **Enterprise Attendance Matrix:** A visually stylized data grid (rows = Students, cols = Calendar Days) with color-coded status indicators ('P', 'A', 'L').
    *   **Complete CRUD Operations:** Add new students, update profiles, or permanently delete students with cascade effects on attendance logs.
    *   **Macro Insights:** Daily average attendance rates and automatic detection of low-attendance warning patterns.
*   **Data Persistence & Mock Data:** Uses `sqlite3` for robust local storage. The app automatically seeds the database with 1 Teacher and 5 Students with 15 days of mock attendance history on the very first run.
*   **Enterprise UI:** Designed to replicate the layout of professional HR tools using `st.dataframe` CSS styling and Plotly interactive charts.

## 📂 Project Structure

Ensure the following files are located in the same directory:

```text
AMS-Streamlit/
├── app.py              # Main integrated application code
├── requirements.txt    # Python dependencies
├── README.md           
└── attendance_system.db # (Automatically created on first run)
