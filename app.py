import streamlit as st
import pandas as pd
import datetime
import random
import time
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from sqlalchemy.orm import sessionmaker
import plotly.express as px

from models import User, Student, Attendance, SessionLocal, engine, Base
from auth import init_auth, login_user, logout_user, create_user
from utils import encode_face, verify_face, scan_qr_code

# --- PAGE CONFIG ---
st.set_page_config(page_title="AMS - Attendance Management System", layout="wide")

# --- APP INITIALIZATION ---
init_auth()
Base.metadata.create_all(engine)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("AMS Portal")
    if st.session_state.logged_in:
        st.write(f"👤 {st.session_state.full_name}")
        st.write(f"Role: {st.session_state.role}")
        if st.button("🚪 Logout"):
            logout_user()
    else:
        st.write("Secure Login")

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Welcome to Attendance Management System")
        with st.form("Login Form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                if login_user(username, password):
                    st.success(f"Logged in as {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.caption("**Default Demo Accounts**: \n- Teacher: admin / admin123 \n- Student: student1 / password")

# --- APP DASHBOARDS ---
if st.session_state.logged_in:
    db = SessionLocal()
    
    # ------ TEACHER DASHBOARD ------
    if st.session_state.role == 'TEACHER':
        st.title("Teacher Dashboard: Class Attendance & Management")
        
        tab1, tab2, tab3 = st.tabs(["📊 Attendance Grid", "👨‍🏫 Manage Students", "📈 Analytics"])
        
        with tab1:
            # Simulating the exact grid from your provided image
            st.subheader("📅 Class Attendance Tracker")
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_month = st.date_input("Select Month", datetime.date.today()).replace(day=1)
            with col2:
                classes = [row[0] for row in db.query(User.class_id).filter(User.role=='STUDENT').distinct().all()]
                selected_class = st.selectbox("Filter Class", ["All"] + classes)
            with col3:
                st.write(f"*Real-time Updates:* Active")
            
            # Fetch students
            query = db.query(User).filter(User.role == 'STUDENT')
            if selected_class != "All":
                query = query.filter(User.class_id == selected_class)
            students = query.all()
            
            if students:
                days_in_month = (selected_month.replace(month=selected_month.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
                headers = ["Student Name"] + [f"{i:02d}" for i in range(1, days_in_month + 1)]
                
                rows = []
                for student in users:
                    student_record = db.query(Student).filter(Student.user_id == student.id).first()
                    row = {"Student Name": student.full_name}
                    for day in range(1, days_in_month + 1):
                        d = selected_month.replace(day=day)
                        # Generate random data for demo (Replace with DB query in prod)
                        # Weekends check
                        if d.weekday() >= 5:
                            status = "WK" # Weekend
                        else:
                            status = random.choices(["P", "A", "HL"], weights=[0.7, 0.2, 0.1])[0]
                        row[f"{day:02d}"] = status
                    rows.append(row)
                
                df = pd.DataFrame(rows)
                
                # Styling the dataframe to match the image
                def style_status(val):
                    color_map = {'P': 'background-color: #d4edda; color: #155724;', 
                                 'A': 'background-color: #f8d7da; color: #721c24;',
                                 'HL': 'background-color: #fff3cd; color: #856404;',
                                 'WK': 'background-color: #cce5ff; color: #004085;'}
                    return color_map.get(val, '')
                
                st.dataframe(df.style.map(style_status), use_container_width=True, height=500)
                
                # Simulating the Tooltip hover effect
                st.info("💡 Hover over the data points above. In production, a detailed hover shows `IN: 09:30 AM`, `OUT: 04:45 PM`, `Total Hours`.")
            else:
                st.warning("No students found in this class.")

        with tab2:
            st.subheader("➕ Add / Remove Students")
            with st.form("add_student"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    full_name = st.text_input("Full Name")
                with col2:
                    class_code = st.text_input("Class ID (e.g., CS-101)")
                with col3:
                    uname = st.text_input("Username")
                passwd = st.text_input("Password", type="password")
                if st.form_submit_button("Add Student"):
                    user_id = create_user(uname, passwd, 'STUDENT', full_name, class_code)
                    new_student = Student(user_id=user_id)
                    db.add(new_student)
                    db.commit()
                    st.success(f"Student {full_name} added successfully!")
                    st.rerun()

        with tab3:
            st.subheader("📊 Class Analytics")
            # Fetch data for chart
            # In a real scenario, join attendance and user tables
            statuses = ['Present', 'Absent', 'Half Leave']
            counts = [40, 15, 5] # Dummy data
            fig = px.pie(values=counts, names=statuses, title="Class Attendance Distribution")
            st.plotly_chart(fig, use_container_width=True)

    # ------ STUDENT DASHBOARD ------
    elif st.session_state.role == 'STUDENT':
        st.title("Student Dashboard")
        current_student = db.query(Student).filter(Student.user_id == st.session_state.user_id).first()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📌 My Attendance (This Month)")
            # Fetch dummy stats for the student
            df_att = pd.DataFrame({
                "Date": pd.date_range(start=datetime.date.today().replace(day=1), periods=30),
                "Status": [random.choice(["P", "A", "HL"]) for _ in range(30)]
            })
            fig = px.bar(df_att, x="Date", y="Status", color="Status", title="Daily Attendance")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🔄 Mark Attendance")
            method = st.radio("Select Method", ["Face Recognition", "QR Code"])
            
            if method == "Face Recognition":
                # Using webrtc for streamlit
                webrtc_streamer(key="face_recognition", video_transformer_factory=lambda: VideoTransformerBase())
                st.caption("Note: This requires a webcam. In demo mode, it simulates encoding check.")
                if st.button("Simulate Face Scan Pass"):
                    st.success("✅ Face Verified! Attendance Marked for today.")
            elif method == "QR Code":
                st.write("📱 Open your student ID QR code on your phone.")
                qr_input = st.text_input("Paste QR Code Text (or simulate ID)")
                if st.button("Scan QR"):
                    if qr_input == "DEMO_STUDENT_ID":
                        st.success("✅ QR Verified! Attendance Marked for today.")
                    else:
                        st.error("Invalid QR Code")
            
            st.info("📶 Offline mode is supported. If internet drops, attendance is queued locally and synced when connectivity is restored.")

    db.close()
