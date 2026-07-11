import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
import os
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple

# --- Configuration & Constants ---
DB_NAME = "attendance_system.db"
DATE_FORMAT = "%Y-%m-%d"

# --- Database Helper Functions ---
def get_db_connection():
    """Returns a thread-safe sqlite3 connection."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'teacher'))
            )
        """)
        # Attendance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Leave')),
                timestamp TEXT NOT NULL,
                is_synced INTEGER DEFAULT 1,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(student_id, date) ON CONFLICT REPLACE
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def hash_password(password: str) -> str:
    """Simulates secure password hashing using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_mock_data():
    """Pre-populate the database with 5 students and 1 teacher, plus 15 days of attendance."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return # Data already seeded

        # 1. Create Teacher
        teacher_pass = hash_password("admin123")
        cursor.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                       ("admin", teacher_pass, "System Administrator", "teacher"))
        
        # 2. Create Students
        student_data = [
            ("student1", hash_password("123456"), "Arham MH"),
            ("student2", hash_password("123456"), "John Doe"),
            ("student3", hash_password("123456"), "Meaghan Campigotto"),
            ("student4", hash_password("123456"), "Evander Deoscariz"),
            ("student5", hash_password("123456"), "Mark Wood")
        ]
        cursor.executemany("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                           [(u, p, n, "student") for u, p, n in student_data])
        
        # 3. Retrieve Student IDs
        cursor.execute("SELECT id, full_name FROM users WHERE role = 'student'")
        students = cursor.fetchall()
        
        # 4. Generate 15 days of mock attendance
        today = datetime.date.today()
        attendance_records = []
        import random
        statuses = ['Present', 'Present', 'Present', 'Absent', 'Leave'] # Weighted towards Present
        
        for student in students:
            s_id = student['id']
            for i in range(15, 0, -1):
                day_date = today - datetime.timedelta(days=i)
                # Ensure date is past or present, not future
                if day_date <= today:
                    status = random.choice(statuses)
                    timestamp = f"{day_date} 09:{random.randint(10, 59):02d}:00"
                    attendance_records.append((s_id, day_date.strftime(DATE_FORMAT), status, timestamp))

        cursor.executemany("INSERT INTO attendance (student_id, date, status, timestamp) VALUES (?, ?, ?, ?)", 
                           attendance_records)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error seeding data: {e}")
    finally:
        conn.close()

# --- Authentication Functions ---
def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Validates credentials and returns user dict or None."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed_input = hash_password(password)
        cursor.execute("SELECT id, username, full_name, role FROM users WHERE username = ? AND password_hash = ?", 
                       (username, hashed_input))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.Error:
        return None
    finally:
        conn.close()

# --- Student Application Functions ---
def student_tab_checkin(student_id: int, student_name: str):
    st.subheader(f"🔐 Secure Digital Check-In: {student_name}")
    st.markdown("---")
    
    today = datetime.date.today().strftime(DATE_FORMAT)
    
    # Check if already checked in today
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM attendance WHERE student_id = ? AND date = ?", (student_id, today))
        record = cursor.fetchone()
        
        if record:
            st.warning(f"⚠️ You have already marked attendance for today as: **{record['status']}**")
            st.info("Duplicate check-ins are prevented automatically.")
            return
    finally:
        conn.close()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Simulated QR / Biometric Check-In")
        st.write("Click the button below to simulate scanning your digital ID card / QR code.")
        
        if st.button("✅ Scan QR Code / Check-In Now", use_container_width=True, type="primary"):
            # Simulate offline handling check
            if "offline_mode" in st.session_state and st.session_state.offline_mode:
                # Offline Mode logic
                offline_entry = {
                    "student_id": student_id,
                    "date": today,
                    "status": "Present",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.offline_cache.append(offline_entry)
                st.success("✅ Attendance marked in **Offline Mode**. Data cached locally.")
                st.info("Data will sync to the server when you disable Offline Mode.")
            else:
                # Online Mode logic
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO attendance (student_id, date, status, timestamp) VALUES (?, ?, ?, ?)",
                                   (student_id, today, "Present", now))
                    conn.commit()
                    st.success("🎉 Attendance marked successfully as **Present**!")
                    st.balloons()
                except sqlite3.Error as e:
                    st.error(f"Error marking attendance: {e}")
                finally:
                    conn.close()

def student_tab_offline(student_id: int):
    st.subheader("📶 Offline Mode Management")
    st.markdown("---")
    
    # Initialize offline cache if not exists
    if "offline_cache" not in st.session_state:
        st.session_state.offline_cache = []
    
    # Offline Toggle
    offline_enabled = st.toggle("Enable Offline Mode", value=st.session_state.get("offline_mode", False))
    st.session_state.offline_mode = offline_enabled
    
    if offline_enabled:
        st.info("🟢 **Offline Mode Active**. Attendance records are saved locally and NOT pushed to the server.")
        
        pending = len(st.session_state.offline_cache)
        st.metric("Pending Offline Records to Sync", pending)
        
        if st.button("🔄 Force Sync Now", type="primary"):
            if pending > 0:
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    records_to_sync = st.session_state.offline_cache
                    cursor.executemany("INSERT INTO attendance (student_id, date, status, timestamp) VALUES (?, ?, ?, ?)",
                                       [(r['student_id'], r['date'], r['status'], r['timestamp']) for r in records_to_sync])
                    conn.commit()
                    st.session_state.offline_cache = [] # Clear cache
                    st.success(f"Successfully synced {pending} records to the cloud/server database!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Failed to sync offline data: {e}")
                finally:
                    conn.close()
            else:
                st.warning("No pending records to sync.")
    else:
        if len(st.session_state.offline_cache) > 0:
            st.warning(f"🔴 Offline mode is disabled, but you have {len(st.session_state.offline_cache)} unsynced records! Re-enable offline mode and click 'Force Sync' to prevent data loss.")
        else:
            st.success("🟢 Online Mode Active. All check-ins are recorded directly to the database.")

def student_tab_stats(student_id: int):
    st.subheader("📊 Personal Attendance Analytics")
    st.markdown("---")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get attendance counts
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM attendance 
            WHERE student_id = ? 
            GROUP BY status
        """, (student_id,))
        rows = cursor.fetchall()
        
        total_present = 0
        total_absent = 0
        total_leave = 0
        
        for row in rows:
            if row['status'] == 'Present': total_present = row['count']
            elif row['status'] == 'Absent': total_absent = row['count']
            elif row['status'] == 'Leave': total_leave = row['count']
        
        total_days = total_present + total_absent + total_leave
        percentage = round((total_present / total_days * 100), 2) if total_days > 0 else 0.0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Days Present", total_present)
        col2.metric("Total Days Absent", total_absent)
        col3.metric("Attendance %", f"{percentage}%")
        
        # Visual Chart (Pie Chart)
        if total_days > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Present', 'Absent', 'Leave'],
                values=[total_present, total_absent, total_leave],
                hole=.3,
                marker=dict(colors=['#28a745', '#dc3545', '#ffc107'])
            )])
            fig.update_layout(title_text="Attendance Distribution", title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
            
            # Historical Trend (Line/Bar Chart)
            cursor.execute("""
                SELECT date, status 
                FROM attendance 
                WHERE student_id = ? 
                ORDER BY date ASC
            """, (student_id,))
            trends = cursor.fetchall()
            if trends:
                df = pd.DataFrame(trends)
                df['status_val'] = df['status'].map({'Present': 1, 'Leave': 0.5, 'Absent': 0})
                fig2 = px.line(df, x='date', y='status_val', title='Attendance Trend (1=Present, 0.5=Leave, 0=Absent)',
                              markers=True, color_discrete_sequence=['#007bff'])
                fig2.update_layout(xaxis_title="Date", yaxis_title="Status Score")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No attendance records found to generate stats.")
    except sqlite3.Error as e:
        st.error(f"Error loading stats: {e}")
    finally:
        conn.close()

# --- Teacher Application Functions ---
def teacher_tab_matrix():
    st.subheader("📅 Enterprise Attendance Matrix")
    st.markdown("---")
    
    today = datetime.date.today()
    start_date = today.replace(day=1)
    
    conn = get_db_connection()
    try:
        # 1. Fetch Students
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name FROM users WHERE role = 'student' ORDER BY full_name")
        students = cursor.fetchall()
        
        if not students:
            st.info("No students found in the system. Please add students first.")
            return

        # 2. Fetch attendance for current month
        cursor.execute("""
            SELECT student_id, date, status 
            FROM attendance 
            WHERE date >= ? AND date <= ?
        """, (start_date.strftime(DATE_FORMAT), today.strftime(DATE_FORMAT)))
        attendance_records = cursor.fetchall()
        
        # 3. Pivot Data into Matrix
        data = []
        days_in_month = today.day # Only up to today
        
        # Map student_id to attendance for quick lookup
        att_map = {}
        for rec in attendance_records:
            key = (rec['student_id'], rec['date'])
            att_map[key] = rec['status']

        for student in students:
            row = {"Student Name": student['full_name']}
            for day in range(1, days_in_month + 1):
                date_str = f"{today.strftime('%Y-%m')}-{day:02d}"
                status = att_map.get((student['id'], date_str), "N/A")
                row[date_str] = status
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # 4. Display with Styler (Highly professional HR view)
        # Define color styling
        def color_status(val):
            color = 'white'
            bg = 'white'
            if val == 'Present':
                bg = '#d4edda' # Light green
                color = 'black'
            elif val == 'Absent':
                bg = '#f8d7da' # Light red
                color = 'black'
            elif val == 'Leave':
                bg = '#fff3cd' # Light yellow
                color = 'black'
            elif val == 'N/A':
                bg = '#f8f9fa' # Light gray
                color = '#6c757d'
            return f'background-color: {bg}; color: {color}; text-align: center; font-weight: bold;'
        
        styled_df = df.style.applymap(color_status, subset=pd.IndexSlice[:, df.columns[1:]])
        
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Summary Stats
        st.markdown("### 📈 Class Summary for Current Month")
        summary_data = {
            "Metric": ["Total Students", "Days Passed", "Average Daily Attendance"],
            "Value": [len(students), days_in_month, "Calculating..."]
        }
        # Calculate average daily attendance
        daily_counts = {}
        for rec in attendance_records:
            d = rec['date']
            if rec['status'] == 'Present':
                daily_counts[d] = daily_counts.get(d, 0) + 1
        total_present = sum(daily_counts.values())
        daily_avg = round(total_present / (len(students) * days_in_month) * 100, 2) if days_in_month > 0 else 0
        summary_data["Value"][2] = f"{daily_avg}%"
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        
    except sqlite3.Error as e:
        st.error(f"Error loading attendance matrix: {e}")
    finally:
        conn.close()

def teacher_tab_crud():
    st.subheader("👨‍🏫 Student Management (CRUD)")
    st.markdown("---")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, username FROM users WHERE role = 'student'")
        students = cursor.fetchall()
        
        # --- ADD STUDENT ---
        with st.expander("➕ Add New Student"):
            with st.form("add_student_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_full_name = st.text_input("Full Name")
                with col2:
                    new_username = st.text_input("Username")
                with col3:
                    new_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Add Student")
                
                if submitted:
                    if not new_full_name or not new_username or not new_password:
                        st.error("All fields are required to add a student.")
                    else:
                        try:
                            hashed = hash_password(new_password)
                            cursor.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                                          (new_username, hashed, new_full_name, "student"))
                            conn.commit()
                            st.success(f"Student '{new_full_name}' added successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Username '{new_username}' is already taken.")
        
        # --- DELETE STUDENT ---
        with st.expander("❌ Remove Student"):
            if students:
                student_options = {f"{s['id']} - {s['full_name']}": s['id'] for s in students}
                selected_student_label = st.selectbox("Select Student to Delete", list(student_options.keys()))
                if st.button("Permanently Delete Student", type="primary", use_container_width=True):
                    student_id = student_options[selected_student_label]
                    try:
                        cursor.execute("DELETE FROM users WHERE id = ?", (student_id,))
                        conn.commit()
                        st.success(f"Student '{selected_student_label}' deleted successfully. (Attendance logs cascade deleted)")
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Error deleting student: {e}")
            else:
                st.info("No students available to delete.")
                
        # --- UPDATE STUDENT ---
        with st.expander("✏️ Update Student Profile"):
            if students:
                update_options = {f"{s['id']} - {s['full_name']}": s for s in students}
                selected_label = st.selectbox("Select Student to Update", list(update_options.keys()))
                selected_student = update_options[selected_label]
                
                with st.form("update_student_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        u_full_name = st.text_input("Update Full Name", value=selected_student['full_name'])
                    with col2:
                        u_username = st.text_input("Update Username", value=selected_student['username'])
                    u_password = st.text_input("New Password (Leave blank to keep current)", type="password")
                    
                    update_btn = st.form_submit_button("Update Student")
                    if update_btn:
                        try:
                            if u_password:
                                hashed = hash_password(u_password)
                                cursor.execute("UPDATE users SET full_name = ?, username = ?, password_hash = ? WHERE id = ?",
                                              (u_full_name, u_username, hashed, selected_student['id']))
                            else:
                                cursor.execute("UPDATE users SET full_name = ?, username = ? WHERE id = ?",
                                              (u_full_name, u_username, selected_student['id']))
                            conn.commit()
                            st.success(f"Student '{u_full_name}' updated successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Username '{u_username}' is already taken.")
            else:
                st.info("No students available to update.")

    except sqlite3.Error as e:
        st.error(f"CRUD operation error: {e}")
    finally:
        conn.close()

def teacher_tab_insights():
    st.subheader("📊 Macro-Level Attendance Insights")
    st.markdown("---")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, 
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                   COUNT(*) as total_records
            FROM attendance
            GROUP BY date
            ORDER BY date ASC
        """)
        data = cursor.fetchall()
        
        if not data:
            st.info("Insufficient data for generating insights.")
            return
            
        df = pd.DataFrame(data)
        df['attendance_rate'] = (df['present_count'] / df['total_records']) * 100
        
        fig = px.bar(df, x='date', y='attendance_rate', 
                     title='Daily Attendance Rate (%)',
                     labels={'attendance_rate': 'Attendance %', 'date': 'Date'},
                     color='attendance_rate', color_continuous_scale='RdYlGn')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Low attendance warning patterns
        avg_att = df['attendance_rate'].mean()
        low_days = df[df['attendance_rate'] < 80]
        st.metric("Overall Average Attendance", f"{avg_att:.2f}%")
        if not low_days.empty:
            st.warning(f"⚠️ Low attendance alerts: {len(low_days)} days recorded below 80% attendance.")
        else:
            st.success("✅ No low attendance warning patterns detected recently.")

    except sqlite3.Error as e:
        st.error(f"Error generating insights: {e}")
    finally:
        conn.close()

# --- Application Layout ---
def main():
    st.set_page_config(page_title="AMS - Attendance Management", layout="wide", page_icon="📋")
    
    # Initialize persistence
    init_database()
    seed_mock_data()
    
    if "offline_cache" not in st.session_state:
        st.session_state.offline_cache = []
    if "user" not in st.session_state:
        st.session_state.user = None

    # --- AUTHENTICATION SCREEN ---
    if st.session_state.user is None:
        st.title("🔐 University Attendance Management System")
        
        with st.container():
            st.subheader("Secure Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submitted:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        
        st.markdown("---")
        st.caption("Default Credentials: Teacher: `admin` / `admin123` | Student: `student1` / `123456`")
        return

    # --- DASHBOARD ---
    user = st.session_state.user
    st.sidebar.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=50)
    st.sidebar.title(f"Welcome, {user['full_name']}")
    st.sidebar.markdown(f"**Role:** {'👨‍🏫 Teacher' if user['role'] == 'teacher' else '🧑‍🎓 Student'}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.offline_cache = []
        st.rerun()

    # --- ROUTING BASED ON ROLE (RBAC) ---
    if user['role'] == 'student':
        tab1, tab2, tab3 = st.tabs(["✅ Check-In", "📶 Offline", "📊 My Stats"])
        with tab1:
            student_tab_checkin(user['id'], user['full_name'])
        with tab2:
            student_tab_offline(user['id'])
        with tab3:
            student_tab_stats(user['id'])
            
    elif user['role'] == 'teacher':
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Attendance Matrix", "👨‍🏫 Manage Students", "📊 Insights", "📁 System"])
        with tab1:
            teacher_tab_matrix()
        with tab2:
            teacher_tab_crud()
        with tab3:
            teacher_tab_insights()
        with tab4:
            st.subheader("System Information")
            st.json({
                "System Status": "Running",
                "Database": "SQLite3",
                "Auth": "Secure Session State",
                "User": user['username']
            })

if __name__ == "__main__":
    main()
