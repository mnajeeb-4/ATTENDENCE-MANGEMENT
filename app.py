import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('attendance_system.db')
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    # Attendance Table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (username TEXT, date TEXT, status TEXT, method TEXT)''')
    conn.commit()
    conn.close()

# --- SECURITY FUNCTIONS ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# --- DATABASE FUNCTIONS ---
def add_user(username, password, role):
    conn = sqlite3.connect('attendance_system.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate(username, password):
    conn = sqlite3.connect('attendance_system.db')
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and check_password(password, result[0]):
        return result[1] # Return role
    return None

def mark_attendance(username, method):
    conn = sqlite3.connect('attendance_system.db')
    c = conn.cursor()
    date_today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if already marked today
    c.execute("SELECT * FROM attendance WHERE username = ? AND date = ?", (username, date_today))
    if c.fetchone():
        conn.close()
        return False
        
    c.execute("INSERT INTO attendance (username, date, status, method) VALUES (?, ?, ?, ?)",
              (username, date_today, "Present", method))
    conn.commit()
    conn.close()
    return True

# --- UI COMPONENTS ---
def student_dashboard(username):
    st.title(f"Welcome Student: {username}")
    st.write("Mark your attendance securely.") # [cite: 25]
    
    # Attendance Variations [cite: 31]
    method = st.radio("Select Attendance Method:", ["QR Code Simulation", "Face Match Simulation"])
    
    if st.button("Mark Attendance"):
        if mark_attendance(username, method):
            st.success(f"Attendance marked successfully via {method}!")
        else:
            st.warning("Attendance already marked for today.")
            
    st.subheader("Your Attendance Statistics") # [cite: 24]
    conn = sqlite3.connect('attendance_system.db')
    df = pd.read_sql_query("SELECT date, status FROM attendance WHERE username = ?", conn, params=(username,))
    conn.close()
    
    if not df.empty:
        st.dataframe(df)
        # Simple Graph
        stats = df['status'].value_counts()
        st.bar_chart(stats)
    else:
        st.info("No attendance records found.")

def teacher_dashboard():
    st.title("Teacher Dashboard")
    st.write("Manage Students & View Analytics") # [cite: 27, 29]
    
    menu = ["View All Attendance", "Register New Student"]
    choice = st.sidebar.selectbox("Teacher Menu", menu)
    
    if choice == "Register New Student":
        st.subheader("Register a Student")
        new_user = st.text_input("New Student Username")
        new_pass = st.text_input("New Student Password", type="password")
        if st.button("Register"):
            if add_user(new_user, new_pass, "Student"):
                st.success("Student registered successfully!")
            else:
                st.error("Username already exists.")
                
    elif choice == "View All Attendance":
        st.subheader("Class Attendance Insights") # [cite: 29]
        conn = sqlite3.connect('attendance_system.db')
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df)
            st.write("Total Attendance per day:")
            date_counts = df.groupby('date').size()
            st.line_chart(date_counts)
        else:
            st.info("No records to display.")

# --- MAIN APP LOGIC ---
def main():
    st.set_page_config(page_title="AMS System", layout="centered")
    init_db()
    
    # Initialize session state for login
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['role'] = ""
        
        # Create a default teacher account for testing
        add_user("teacher1", "admin123", "Teacher")

    if not st.session_state['logged_in']:
        st.title("Login to AMS") # Secure Authentication [cite: 41, 68]
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            role = authenticate(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    else:
        # Sidebar Logout
        st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
        
        # Route based on role
        if st.session_state['role'] == "Student":
            student_dashboard(st.session_state['username']) # [cite: 46]
        elif st.session_state['role'] == "Teacher":
            teacher_dashboard() # [cite: 47]

if __name__ == '__main__':
    main()
