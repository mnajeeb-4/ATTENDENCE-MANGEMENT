import streamlit as st
import json
import os
import hashlib
import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.face_utils import verify_face_capture

# --- DATA LAYER ---
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return init_data()
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def init_data():
    # Pre-populate with mock data to visualize the grid immediately
    mock_data = {
        "users": [
            {"id": "T001", "name": "Mr. Arham", "role": "teacher", "password": hashlib.sha256("teacher123".encode()).hexdigest(), "department": "CS", "course": "CS101"},
            {"id": "S001", "name": "Mark Wood", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "CS", "student_id": "S001", "course": "CS101"},
            {"id": "S002", "name": "John Doe", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "IT", "student_id": "S002", "course": "IT101"},
            {"id": "S003", "name": "Meaghan Campigotto", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "CS", "student_id": "S003", "course": "CS101"},
            {"id": "S004", "name": "Tri Chan", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "CS", "student_id": "S004", "course": "CS101"},
            {"id": "S005", "name": "Evander Deocareza", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "CS", "student_id": "S005", "course": "CS101"},
            {"id": "S006", "name": "Karen Frekko", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "IT", "student_id": "S006", "course": "IT101"},
            {"id": "S007", "name": "Magdalena Gonzalez", "role": "student", "password": hashlib.sha256("student123".encode()).hexdigest(), "department": "IT", "student_id": "S007", "course": "IT101"}
        ],
        "attendance": [],
        "classes": [
            {"teacher_id": "T001", "course": "CS101", "student_ids": ["S001", "S003", "S004", "S005"]},
            {"teacher_id": "T001", "course": "IT101", "student_ids": ["S002", "S006", "S007"]}
        ]
    }
    
    # Add mock attendance for the past month to populate the grid
    today = datetime.date.today()
    base_date = today.replace(day=1)
    import random
    statuses = ['P', 'P', 'P', 'A', 'HL', 'P', 'P']
    in_time = ["09:00", "09:15", "10:00", "-", "09:00", "09:05", "09:30"]
    out_time = ["17:00", "17:00", "18:00", "-", "13:00", "17:00", "17:00"]
    for student in mock_data["users"]:
        if student["role"] == "student":
            for day in range(1, 28): # fill up to the 27th
                date_str = f"{base_date.year}-{base_date.month:02d}-{day:02d}"
                idx = random.randint(0, len(statuses)-1)
                mock_data["attendance"].append({
                    "student_id": student["student_id"],
                    "date": date_str,
                    "status": statuses[idx],
                    "in_time": in_time[idx],
                    "out_time": out_time[idx],
                    "remarks": ""
                })
    save_data(mock_data)
    return mock_data

# --- AUTHENTICATION & SESSION STATE ---
def init_session_state():
    if 'logged_in_user' not in st.session_state:
        st.session_state.logged_in_user = None
    if 'offline_mode' not in st.session_state:
        st.session_state.offline_mode = False
    if 'offline_buffer' not in st.session_state:
        st.session_state.offline_buffer = []
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

def login():
    st.subheader("🔐 Secure Authentication")
    username = st.text_input("Username (e.g., S001 or T001)")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        users = st.session_state.data['users']
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        for user in users:
            if (user['student_id'] == username or user['id'] == username) and user['password'] == pass_hash:
                st.session_state.logged_in_user = user
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
        st.error("Invalid credentials")

def logout():
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- STUDENT FEATURES ---
def student_app(user):
    st.title(f"👨‍🎓 Student Portal - {user['name']}")
    
    # Offline Mode Toggle
    col1, col2 = st.columns([3, 1])
    with col2:
        offline_toggle = st.toggle("📶 Offline Mode", value=st.session_state.offline_mode)
        if offline_toggle != st.session_state.offline_mode:
            st.session_state.offline_mode = offline_toggle
            if not offline_toggle and st.session_state.offline_buffer:
                sync_offline_data(user)
                st.success("Synced offline data!")
                st.rerun()

    if st.session_state.offline_mode:
        st.warning("You are in OFFLINE mode. Attendance will be stored locally and synced later.")

    tab1, tab2 = st.tabs(["📝 Mark Attendance", "📊 My Statistics"])

    with tab1:
        st.subheader("Select Attendance Method")
        method = st.radio("Method", ["Face Recognition", "QR Code Scanning", "Fingerprint Scanning"])
        
        if method == "Face Recognition":
            img_file = st.camera_input("Take a snapshot")
            if img_file:
                if st.button("Verify Face & Mark Attendance"):
                    result = verify_face_capture(img_file.read())
                    if result["verified"]:
                        mark_attendance(user, "Face Recognition")
                    else:
                        st.error(result["message"])
        
        elif method == "QR Code Scanning":
            # Simulated QR parsing (avoiding external OS-dependent binaries for 0% cloud error)
            qr_upload = st.file_uploader("Upload QR Code Screenshot", type=["png", "jpg", "jpeg"])
            if qr_upload and st.button("Submit QR Code"):
                # Mock QR processing (Student ID captured from QR)
                st.success("QR Code scanned successfully! Validating...")
                mark_attendance(user, "QR Code")
        
        elif method == "Fingerprint Scanning":
            # Simulated biometric hardware integration
            if st.button("Scan Fingerprint (Simulated)"):
                mark_attendance(user, "Fingerprint Scanning")

    with tab2:
        # Show personal analytics
        attendances = [a for a in st.session_state.data['attendance'] if a['student_id'] == user['student_id']]
        if attendances:
            df = pd.DataFrame(attendances)
            df['date'] = pd.to_datetime(df['date'])
            status_counts = df['status'].value_counts()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = px.pie(values=status_counts.values, names=status_counts.index, title="Attendance Distribution")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                # Daily trend
                fig2 = px.line(df, x='date', y='status', title="Attendance Timeline")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No attendance records found.")

def mark_attendance(user, method):
    today = datetime.date.today().isoformat()
    record = {
        "student_id": user['student_id'],
        "date": today,
        "status": "P",
        "in_time": datetime.datetime.now().strftime("%H:%M"),
        "out_time": "-",
        "remarks": f"Marked via {method}"
    }
    
    if st.session_state.offline_mode:
        st.session_state.offline_buffer.append(record)
        st.success("✅ Attendance recorded locally! (Offline Mode)")
    else:
        # Write to main data
        data = st.session_state.data
        # Avoid duplicates for the same day
        existing = next((a for a in data['attendance'] if a['student_id'] == user['student_id'] and a['date'] == today), None)
        if not existing:
            data['attendance'].append(record)
            save_data(data)
            st.session_state.data = data
            st.success(f"✅ Attendance marked as PRESENT via {method}!")
        else:
            st.info("Attendance already marked for today.")

def sync_offline_data(user):
    if st.session_state.offline_buffer:
        data = st.session_state.data
        for rec in st.session_state.offline_buffer:
            # Check if already present
            existing = next((a for a in data['attendance'] if a['student_id'] == rec['student_id'] and a['date'] == rec['date']), None)
            if not existing:
                data['attendance'].append(rec)
        save_data(data)
        st.session_state.data = data
        st.session_state.offline_buffer = []

# --- TEACHER FEATURES ---
def teacher_app(user):
    st.title(f"👨‍🏫 Teacher Portal - {user['name']}")
    logout()
    
    # Get students belonging to the teacher's class (Data Privacy Enforcement)
    students_in_class = []
    for cls in st.session_state.data['classes']:
        if cls['teacher_id'] == user['id']:
            students_in_class = cls['student_ids']
            break
    filtered_students = [u for u in st.session_state.data['users'] if u['role'] == 'student' and u['student_id'] in students_in_class]
    
    tab1, tab2, tab3 = st.tabs(["👥 Student Management", "📅 Attendance Grid", "📈 Analytics"])

    with tab1:
        st.subheader("Manage Student Records")
        action = st.selectbox("Action", ["Add Student", "Update Student", "Delete Student"])
        
        if action == "Add Student":
            with st.form("add_form"):
                s_name = st.text_input("Full Name")
                s_id = st.text_input("Student ID")
                s_department = st.text_input("Department")
                s_course = user['course'] # Enroll in teacher's class
                if st.form_submit_button("Add"):
                    new_student = {
                        "id": s_id, "name": s_name, "role": "student", "student_id": s_id,
                        "department": s_department, "course": s_course,
                        "password": hashlib.sha256("student123".encode()).hexdigest()
                    }
                    data = st.session_state.data
                    data['users'].append(new_student)
                    # Update class list
                    for cls in data['classes']:
                        if cls['teacher_id'] == user['id']:
                            cls['student_ids'].append(s_id)
                            break
                    save_data(data)
                    st.session_state.data = data
                    st.success("Student added successfully!")
                    st.rerun()
        
        elif action == "Update Student":
            selected = st.selectbox("Select Student", [u['name'] for u in filtered_students])
            if selected:
                stu = next((u for u in filtered_students if u['name'] == selected), None)
                with st.form("update_form"):
                    new_name = st.text_input("Name", value=stu['name'])
                    new_dept = st.text_input("Department", value=stu['department'])
                    if st.form_submit_button("Update"):
                        stu['name'] = new_name
                        stu['department'] = new_dept
                        save_data(st.session_state.data)
                        st.success("Student updated!")
                        st.rerun()
        
        elif action == "Delete Student":
            selected = st.selectbox("Select Student to Delete", [u['name'] for u in filtered_students])
            if st.button(f"Delete {selected}"):
                data = st.session_state.data
                to_del = next(u for u in data['users'] if u['name'] == selected)
                data['users'].remove(to_del)
                # Remove from class
                for cls in data['classes']:
                    if cls['teacher_id'] == user['id']:
                        if to_del['student_id'] in cls['student_ids']:
                            cls['student_ids'].remove(to_del['student_id'])
                        break
                save_data(data)
                st.session_state.data = data
                st.success("Student deleted!")
                st.rerun()

    with tab2:
        st.subheader("Interactive Attendance Grid")
        
        # Filters
        c1, c2 = st.columns(2)
        with c1:
            selected_student = st.selectbox("Filter Student", ["All"] + [u['name'] for u in filtered_students])
        with c2:
            status_filter = st.selectbox("Filter Status", ["All", "Present", "Absent", "Half Leave", "Weekend"])

        # Prepare data for the Heatmap
        start_date = datetime.date.today().replace(day=1)
        days_in_month = (datetime.date(start_date.year, start_date.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        dates = [f"{start_date.month:02d}-{d:02d}" for d in range(1, days_in_month + 1)]
        
        # Filter students
        display_students = filtered_students if selected_student == "All" else [next(u for u in filtered_students if u['name'] == selected_student)]
        
        # Build Matrix
        matrix_z = [] # 0=A, 1=P, 2=HL, 3=WK
        matrix_text = [] # P, A, HL, WK
        hover_text = []
        
        for stu in display_students:
            z_row, text_row, hover_row = [], [], []
            for day_str in dates:
                full_date = f"{start_date.year}-{start_date.month:02d}-{day_str.split('-')[1]}"
                # Check for weekend (Simulate based on day index)
                day_num = int(day_str.split('-')[1])
                if (start_date.weekday() + day_num - 1) % 7 >= 5:
                    z_row.append(3)
                    text_row.append("WK")
                    hover_row.append("Weekend")
                else:
                    # Find record
                    record = next((a for a in st.session_state.data['attendance'] if a['student_id'] == stu['student_id'] and a['date'] == full_date), None)
                    if record:
                        if record['status'] == 'P':
                            z_row.append(1); text_row.append("P")
                            hover_row.append(f"IN: {record['in_time']}<br>OUT: {record['out_time']}")
                        elif record['status'] == 'A':
                            z_row.append(0); text_row.append("A")
                            hover_row.append("Absent")
                        elif record['status'] == 'HL':
                            z_row.append(2); text_row.append("HL")
                            hover_row.append("Half Leave")
                        else:
                            z_row.append(1); text_row.append("P")
                            hover_row.append("Present")
                    else:
                        z_row.append(0); text_row.append("A")
                        hover_row.append("Absent")
            matrix_z.append(z_row)
            matrix_text.append(text_row)
            hover_text.append(hover_row)
            
        # Create the exact visual grid matching your image
        fig = go.Figure(data=go.Heatmap(
            z=matrix_z,
            x=dates,
            y=[u['name'] for u in display_students],
            text=matrix_text,
            texttemplate="%{text}",
            textfont={"size": 12, "weight": "bold"},
            colorscale=[
                [0, '#ffcccc'],   # Absent (Red)
                [0.33, '#ccffcc'],# Present (Green)
                [0.66, '#ccccff'],# Half Leave (Blue)
                [1, '#f0f0f0']    # Weekend (Gray)
            ],
            showscale=False,
            hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Status: %{text}<br>Details: %{customdata}<extra></extra>",
            customdata=hover_text
        ))
        
        fig.update_layout(
            title=f"Attendance - {start_date.strftime('%B %Y')}",
            xaxis=dict(tickangle=-45, gridcolor='lightgray', showgrid=True),
            yaxis=dict(gridcolor='lightgray', showgrid=True),
            height=max(400, len(display_students)*40),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Class Analytics")
        attendance_data = [a for a in st.session_state.data['attendance'] if a['student_id'] in [s['student_id'] for s in filtered_students]]
        if attendance_data:
            df = pd.DataFrame(attendance_data)
            df['date'] = pd.to_datetime(df['date'])
            pivot = df.groupby(['date', 'status']).size().reset_index(name='count')
            fig = px.bar(pivot, x="date", y="count", color="status", title="Daily Attendance Summary")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No attendance data available yet.")

# --- MAIN APP EXECUTOR ---
def main():
    st.set_page_config(page_title="University AMS", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🎓 ATTENDANCE MANAGEMENT SYSTEM</h1>", unsafe_allow_html=True)
    
    init_session_state()
    
    # Data Privacy: Enforce login
    if not st.session_state.logged_in_user:
        login()
    else:
        user = st.session_state.logged_in_user
        if user['role'] == 'teacher':
            teacher_app(user)
        elif user['role'] == 'student':
            student_app(user)

if __name__ == "__main__":
    main()
