# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import calendar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from models import Base, User, Attendance
import io
from PIL import Image
from pyzbar.pyzbar import decode

# --- 1. DATABASE SETUP (SQLite for simplicity) ---
engine = create_engine('sqlite:///ams.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# --- 2. SEED TEST DATA (Run only once) ---
if not db.query(User).filter_by(username='teacher1').first():
    db.add(User(username='teacher1', password=generate_password_hash('123'), role='teacher', full_name='Mr. Smith', class_name='Class A'))
    db.add(User(username='student1', password=generate_password_hash('123'), role='student', full_name='John Doe', class_name='Class A'))
    db.commit()

# --- 3. STREAMLIT APP START ---
st.set_page_config(layout="wide", page_title="AMS System")

# --- 4. AUTHENTICATION ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'offline_queue' not in st.session_state:
    st.session_state.offline_queue = [] # For offline mode

def login():
    st.title("Attendance Management System")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = db.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                st.session_state.user_id = user.id
                st.session_state.role = user.role
                st.session_state.full_name = user.full_name
                st.session_state.class_name = user.class_name
                st.rerun()
            else:
                st.error("Invalid credentials")

if st.session_state.user_id is None:
    login()
    st.stop()

# --- 5. TEACHER DASHBOARD ---
def teacher_dashboard():
    st.sidebar.title(f"👨‍🏫 Teacher: {st.session_state.full_name}")
    if st.sidebar.button("Logout"):
        for key in ['user_id', 'role', 'full_name', 'class_name']:
            st.session_state.pop(key)
        st.rerun()

    st.header("📊 Attendance Grid")
    current_user = db.query(User).filter_by(id=st.session_state.user_id).first()
    
    # Get students from teacher's class only (RBAC)
    students = db.query(User).filter_by(role='student', class_name=current_user.class_name).all()
    
    today = date.today()
    year, month = today.year, today.month
    
    # --- 6. RENDER GRID WITH CUSTOM HTML & TOOLTIPS ---
    def render_grid_html():
        # Get month details
        num_days = calendar.monthrange(year, month)[1]
        
        html = """
        <style>
            .grid-table { border-collapse: collapse; width: 100%; font-family: Arial; font-size: 12px; }
            .grid-table th, .grid-table td { border: 1px solid #ddd; padding: 4px; text-align: center; min-width: 25px; position: relative; }
            .grid-table th { background-color: #f2f2f2; font-weight: bold; }
            .status-P { background-color: #d4edda; color: #155724; }
            .status-A { background-color: #f8d7da; color: #721c24; }
            .status-WK { background-color: #f1f1f1; color: #666; }
            .status-HL { background-color: #fff3cd; color: #856404; }
            
            /* Tooltip CSS */
            .hover-tooltip {
                position: absolute;
                background: #333;
                color: #fff;
                padding: 8px 10px;
                border-radius: 4px;
                display: none;
                width: 160px;
                text-align: left;
                font-size: 11px;
                top: 25px;
                left: -40px;
                z-index: 100;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .grid-table td:hover .hover-tooltip { display: block; }
        </style>
        <table class="grid-table">
            <thead><tr><th>Name</th>
        """
        for d in range(1, num_days+1):
            html += f"<th>{d:02d}</th>"
        html += "</tr></thead><tbody>"

        for student in students:
            html += f"<tr><td style='font-weight:bold; text-align:left;'>{student.full_name}</td>"
            for d in range(1, num_days+1):
                dt = date(year, month, d)
                record = db.query(Attendance).filter_by(user_id=student.id, date=dt).first()
                
                if record:
                    status_class = f"status-{record.status}"
                    # Tooltip logic
                    tooltip_data = f"""
                    <div class='hover-tooltip'>
                        <b>IN:</b> {record.in_time.strftime('%I:%M %p') if record.in_time else '-'}<br>
                        <b>OUT:</b> {record.out_time.strftime('%I:%M %p') if record.out_time else '-'}<br>
                        <b>Total Hrs:</b> {record.total_hours}H<br>
                        <b>Late Hrs:</b> {record.late_hours}H
                    </div>
                    """
                    html += f"<td class='{status_class}'>"
                    html += f"{record.status}" + tooltip_data
                    html += "</td>"
                else:
                    # Weekend logic
                    if dt.weekday() >= 5:
                        html += f"<td class='status-WK'>WK</td>"
                    else:
                        html += f"<td class='status-A'>A</td>"
            html += "</tr>"
        html += "</tbody></table>"
        return html

    # Display the grid
    st.markdown(render_grid_html(), unsafe_allow_html=True)

# --- 7. STUDENT DASHBOARD ---
def student_dashboard():
    st.sidebar.title(f"👨‍🎓 Student: {st.session_state.full_name}")
    if st.sidebar.button("Logout"):
        for key in ['user_id', 'role', 'full_name', 'class_name']:
            st.session_state.pop(key)
        st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📷 Mark Attendance via QR")
        st.info("Upload an image of a QR code OR type your Student ID manually below.")
        
        # QR Upload or Manual
        uploaded_file = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg'])
        user_id_manual = st.text_input("Or Enter Student ID Manually:")
        
        # Process marking
        user_id = None
        if uploaded_file:
            try:
                img = Image.open(uploaded_file)
                decoded_objects = decode(img)
                if decoded_objects:
                    user_id = decoded_objects[0].data.decode('utf-8')
                    st.success(f"Scanned ID: {user_id}")
                else:
                    st.error("No QR code found in image")
            except Exception as e:
                st.error(f"Error reading QR: {e}")
        elif user_id_manual:
            user_id = user_id_manual

        # Offline / Online Marking logic
        if st.button("Mark Attendance"):
            if not user_id:
                st.error("Please provide a valid Student ID")
            else:
                current_user = db.query(User).filter_by(id=int(user_id)).first()
                if not current_user:
                    st.error("Invalid Student ID")
                else:
                    # Check network (simulated via st.session_state)
                    # For offline simulation: we just add to queue and process later
                    st.session_state.offline_queue.append(int(user_id))
                    st.success("Attendance queued! (Offline mode simulated)")
                    st.rerun()

        # Process offline sync (like reconnecting to internet)
        if st.button("📡 Sync Pending Attendance (Simulate Internet Restore)"):
            if not st.session_state.offline_queue:
                st.warning("No pending records")
            else:
                for uid in st.session_state.offline_queue:
                    today = date.today()
                    att = Attendance(
                        user_id=uid,
                        date=today,
                        status='P',
                        in_time=datetime.now().time(),
                        total_hours=9.0,
                        late_hours=0.0
                    )
                    db.add(att)
                    db.commit()
                st.session_state.offline_queue = []
                st.success(f"Synced {len(st.session_state.offline_queue)} records!")
                st.rerun()

    with col2:
        st.subheader("📈 My Personal Stats")
        current_user = db.query(User).filter_by(id=st.session_state.user_id).first()
        records = db.query(Attendance).filter_by(user_id=current_user.id).all()
        present = len([r for r in records if r.status == 'P'])
        absent = len([r for r in records if r.status == 'A'])
        
        if present == 0 and absent == 0:
            st.info("No attendance records yet.")
        else:
            chart_data = pd.DataFrame({
                'Status': ['Present', 'Absent'],
                'Count': [present, absent]
            })
            fig = px.pie(chart_data, names='Status', values='Count', color='Status', 
                         color_discrete_map={'Present':'#4CAF50', 'Absent':'#f44336'})
            st.plotly_chart(fig, use_container_width=True)

# --- 8. MAIN ROUTER ---
if st.session_state.role == 'teacher':
    teacher_dashboard()
elif st.session_state.role == 'student':
    student_dashboard()
