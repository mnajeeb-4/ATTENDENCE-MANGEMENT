# ATTENDENCE-MANGEMENT
# Attendance Management System (AMS) - Student & Teacher Portal

A fully functional, secure Role-Based Access Control (RBAC) Attendance Management System built with Python, Streamlit, OpenCV, and SQLAlchemy. Supports Face Recognition and QR code scanning, omitting fingerprinting as requested.

## 🚀 Features Implemented

1. **Secure Authentication**:
   - Password hashing using `bcrypt`.
   - Session persistence via `st.session_state`.
2. **Role-Based Access**:
   - **Student**: View personal attendance stats, mark attendance via Face or QR.
   - **Teacher**: Manage students (CRUD), view visual monthly grid, analyze trends.
3. **Attendance Modes**:
   - **Face Recognition**: Using OpenCV and `face_recognition`. The encoding is stored in the database and verified.
   - **QR Code Scanning**: Using `qrcode` and `pyzbar`.
4. **Data Privacy**:
   - Students see strictly their own data.
   - Teachers are restricted to their assigned class.
5. **Interactive Visuals**:
   - Styled `st.dataframe` mimicking the provided dashboard (P/A/HL/WK color coding).
   - Plotly graphs for statistics.

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ams-streamlit.git
   cd ams-streamlit
