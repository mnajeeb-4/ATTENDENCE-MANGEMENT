import streamlit as st
import pandas as pd
import plotly.express as px
import random
import datetime
import numpy as np

# --- SETUP ---
st.set_page_config(page_title="Attendance Management System", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_student_id' not in st.session_state:
    st.session_state.current_student_id = None
if 'students_df' not in st.session_state:
    # Mock Data: Initial Student List
    mock_students = [
        {"ID": "S001", "Name": "Alice Johnson", "Class": "10-A", "Department": "Science"},
        {"ID": "S002", "Name": "Bob Smith", "Class": "10-A", "Department": "Science"},
        {"ID": "S003", "Name": "Charlie Davis", "Class": "10-B", "Department": "Arts"},
        {"ID": "S004", "Name": "Diana Ross", "Class": "10-B", "Department": "Arts"},
        {"ID": "S005", "Name": "Evan Wright", "Class": "10-A", "Department": "Science"},
    ]
    st.session_state.students_df = pd.DataFrame(mock_students)

if 'attendance_data' not in st.session_state:
    # Structure: {date: {student_id: {"status": "P|A|HL|WK", "in": "HH:MM", "out": "HH:MM", "hours": float}}}
    st.session_state.attendance_data = {}

if 'offline_queue' not in st.session_state:
    st.session_state.offline_queue = []  # Queue to simulate offline sync

# --- MOCK DATA GENERATORS ---
def get_dates_in_month():
    today = datetime.date.today()
    start = today.replace(day=1)
    next_month = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year+1, month=1, day=1)
    days = (next_month - start).days
    return [start + datetime.timedelta(days=i) for i in range(days)]

def generate_mock_attendance():
    if st.session_state.attendance_data:
        return
    dates = get_dates_in_month()
    statuses = ["P", "A", "HL", "WK"]
    students = st.session_state.students_df.to_dict('records')
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        st.session_state.attendance_data[date_str] = {}
        for student in students:
            status = random.choice(statuses)
            in_time = f"{random.randint(8, 10):02d}:{random.randint(0, 59):02d}"
            out_time = f"{random.randint(16, 18):02d}:{random.randint(0, 59):02d}"
            # Calculate working hours
            hours = round(random.uniform(6.0, 8.5), 1)
            st.session_state.attendance_data[date_str][student['ID']] = {
                "status": status,
                "in": in_time,
                "out": out_time,
                "hours": hours
            }

# Initialize attendance if empty
generate_mock_attendance()

# --- UI HELPER FUNCTIONS ---
def display_logout():
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

# --- LOGIN SYSTEM ---
def login_page():
    st.title("🎓 Attendance Management System")
    st.write("Please log in to continue.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        role = st.radio("Select Role", ["Student", "Teacher"])
        username = st.text_input("Username (Teacher: admin / Student: S001-S005)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Simple Role-Based Access logic (to prevent errors)
            if role == "Teacher" and username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.role = "Teacher"
                st.rerun()
            elif role == "Student" and username in st.session_state.students_df['ID'].values and password == "student123":
                st.session_state.logged_in = True
                st.session_state.role = "Student"
                st.session_state.current_student_id = username
                st.rerun()
            else:
                st.error("Invalid credentials. Teacher: admin/admin123, Student: S001-S005/student123")
    with col2:
        st.info("🔒 **Data Privacy:** Strict RBAC (Role-Based Access Control) is implemented. Students will only view their own records.")

# --- TEACHER DASHBOARD ---
def teacher_dashboard():
    st.title(f"📋 Teacher Dashboard - {datetime.date.today().strftime('%B %Y')}")
    display_logout()

    tab1, tab2, tab3 = st.tabs(["📊 Attendance Grid", "👨‍🎓 Manage Students", "📈 Class Analytics"])

    with tab1:
        st.subheader("Monthly Attendance Grid")
        st.caption("Click a specific student's cell to view exact working hours and timestamps.")
        
        # Prepare Data for Grid
        students = st.session_state.students_df
        dates = sorted(st.session_state.attendance_data.keys())
        
        # Convert to pivotable DataFrame for display
        grid_data = []
        for _, student in students.iterrows():
            row = {"Student": student['Name'], "ID": student['ID']}
            for date in dates:
                record = st.session_state.attendance_data[date].get(student['ID'], {"status": "-"})
                row[date] = record['status']
            grid_data.append(row)
        
        grid_df = pd.DataFrame(grid_data)
        
        # Color styling for the grid
        def color_status(val):
            color = 'white'
            if val == 'P': color = '#d4edda' # Green
            elif val == 'A': color = '#f8d7da' # Red
            elif val == 'HL': color = '#fff3cd' # Yellow
            elif val == 'WK': color = '#e2e3e5' # Grey
            return f'background-color: {color}'

        styled_grid = grid_df.style.map(color_status, subset=grid_df.columns[2:])
        
        # Display Grid
        st.dataframe(styled_grid, use_container_width=True, height=400)
        
        # INTERACTION: Selected Student Details (Hover/Click equivalent)
        st.subheader("📌 Daily Details")
        selected_date = st.selectbox("Select a Date to view detailed timestamps for that day", dates)
        if selected_date:
            day_data = st.session_state.attendance_data[selected_date]
            detail_rows = []
            for s_id, details in day_data.items():
                student_name = st.session_state.students_df[st.session_state.students_df['ID'] == s_id]['Name'].values[0]
                detail_rows.append({
                    "Student": student_name,
                    "Status": details['status'],
                    "IN Time": details['in'],
                    "OUT Time": details['out'],
                    "Total Working Hours": f"{details['hours']} Hours"
                })
            st.dataframe(pd.DataFrame(detail_rows), use_container_width=True)

    with tab2:
        st.subheader("Student Management (CRUD)")
        col_add1, col_add2 = st.columns([2, 1])
        with col_add1:
            new_name = st.text_input("Full Name")
            new_class = st.text_input("Class (e.g., 10-A)")
            new_dept = st.text_input("Department")
            if st.button("Add Student"):
                new_id = f"S{len(st.session_state.students_df) + 1:03d}"
                new_row = pd.DataFrame({"ID": [new_id], "Name": [new_name], "Class": [new_class], "Department": [new_dept]})
                st.session_state.students_df = pd.concat([st.session_state.students_df, new_row], ignore_index=True)
                st.success(f"Added {new_name}")
                st.rerun()
        
        st.dataframe(st.session_state.students_df, use_container_width=True)
        
        delete_id = st.selectbox("Select Student ID to Delete", st.session_state.students_df['ID'].values)
        if st.button("Delete Student"):
            st.session_state.students_df = st.session_state.students_df[st.session_state.students_df['ID'] != delete_id]
            # Also delete their attendance records
            for date in st.session_state.attendance_data:
                if delete_id in st.session_state.attendance_data[date]:
                    del st.session_state.attendance_data[date][delete_id]
            st.success("Student deleted.")
            st.rerun()

    with tab3:
        st.subheader("📊 Class Attendance Analytics")
        class_filter = st.selectbox("Select Class", st.session_state.students_df['Class'].unique())
        filtered_students = st.session_state.students_df[st.session_state.students_df['Class'] == class_filter]
        
        total_p = 0
        total_a = 0
        total_hl = 0
        
        for _, student in filtered_students.iterrows():
            for date in st.session_state.attendance_data:
                record = st.session_state.attendance_data[date].get(student['ID'])
                if record:
                    if record['status'] == 'P': total_p += 1
                    elif record['status'] == 'A': total_a += 1
                    elif record['status'] == 'HL': total_hl += 1
        
        chart_data = pd.DataFrame({
            "Status": ["Present", "Absent", "Half Leave"],
            "Count": [total_p, total_a, total_hl]
        })
        fig = px.pie(chart_data, values='Count', names='Status', color='Status', color_discrete_map={'Present':'#28a745','Absent':'#dc3545','Half Leave':'#ffc107'})
        st.plotly_chart(fig, use_container_width=True)

# --- STUDENT DASHBOARD ---
def student_dashboard():
    student_id = st.session_state.current_student_id
    student_name = st.session_state.students_df[st.session_state.students_df['ID'] == student_id]['Name'].values[0]
    
    st.title(f"👨‍🎓 Student Dashboard - {student_name}")
    display_logout()
    
    st.markdown(f"**ID:** {student_id} | **Class:** {st.session_state.students_df[st.session_state.students_df['ID'] == student_id]['Class'].values[0]}")
    
    tab1, tab2 = st.tabs(["📌 Mark Attendance & Offline Sync", "📈 My Statistics"])
    
    with tab1:
        st.subheader("Mark Attendance (Simulated)")
        st.info("Face Recognition, Fingerprint and QR Code methods have been disabled to ensure zero errors on Streamlit Cloud.")
        st.warning("Simulating Biometric Attendance by clicking button below.")
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        if st.button("Mark Attendance Now (Simulate Scan)"):
            if today in st.session_state.attendance_data:
                # Check if already marked
                if st.session_state.attendance_data[today].get(student_id):
                    st.error("Attendance already marked for today!")
                else:
                    # Simulate marking
                    in_time = datetime.datetime.now().strftime("%H:%M")
                    st.session_state.attendance_data[today][student_id] = {
                        "status": "P",
                        "in": in_time,
                        "out": "-",
                        "hours": 0.0
                    }
                    st.success(f"Attendance marked for {today} at {in_time}")
                    st.rerun()
            else:
                # If date doesn't exist, create it
                st.session_state.attendance_data[today] = {student_id: {"status": "P", "in": "09:00", "out": "-", "hours": 0.0}}
                st.success("Attendance marked for today!")
        
        st.subheader("Offline Mode")
        if st.checkbox("Enable Offline Mode (Simulated)"):
            st.session_state.offline_queue.append({
                "student_id": student_id,
                "date": today,
                "action": "mark_attendance"
            })
            st.success("Attendance saved locally! It will sync when the connection is restored.")

    with tab2:
        st.subheader("My Attendance Statistics")
        
        # Gather own data
        my_statuses = []
        for date, records in st.session_state.attendance_data.items():
            if student_id in records:
                my_statuses.append(records[student_id]['status'])
        
        if not my_statuses:
            st.info("No attendance records found.")
        else:
            count_p = my_statuses.count('P')
            count_a = my_statuses.count('A')
            count_hl = my_statuses.count('HL')
            
            student_chart_data = pd.DataFrame({
                "Status": ["Present", "Absent", "Half Leave"],
                "Count": [count_p, count_a, count_hl]
            })
            fig = px.pie(student_chart_data, values='Count', names='Status', title="Personal Attendance Breakdown")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show a personal log
            log_data = []
            for date, records in st.session_state.attendance_data.items():
                if student_id in records:
                    rec = records[student_id]
                    log_data.append({"Date": date, "Status": rec['status'], "IN": rec['in'], "OUT": rec['out'], "Hours": rec['hours']})
            
            st.dataframe(pd.DataFrame(log_data), use_container_width=True)

# --- MAIN APPLICATION CONTROLLER ---
if not st.session_state.logged_in:
    login_page()
elif st.session_state.role == "Teacher":
    teacher_dashboard()
elif st.session_state.role == "Student":
    student_dashboard()
