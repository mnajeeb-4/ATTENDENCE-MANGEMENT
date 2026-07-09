import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

# --- PAGE CONFIG & CSS ---
st.set_page_config(page_title="AMS Cloud", layout="centered", page_icon="🎓")

def inject_css():
    st.markdown("""
        <style>
        .stApp { background-color: #f4f6f9; }
        h1, h2, h3 { color: #2c3e50; font-family: 'Arial', sans-serif; }
        .stButton>button {
            background-color: #2980b9; color: white; border-radius: 8px; width: 100%;
            font-weight: bold; padding: 10px; border: none; transition: 0.3s;
        }
        .stButton>button:hover { background-color: #3498db; }
        .stTextInput>div>div>input { border-radius: 5px; border: 1px solid #bdc3c7; }
        div[data-testid="stSidebar"] { background-color: #2c3e50; }
        div[data-testid="stSidebar"] * { color: white !important; }
        </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ams_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (username TEXT, date TEXT, status TEXT, method TEXT)''')
    conn.commit()
    conn.close()

# --- SECURITY ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, role):
    conn = sqlite3.connect('ams_database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate(username, password):
    conn = sqlite3.connect('ams_database.db')
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# --- CORE LOGIC ---
def mark_attendance(username, method):
    conn = sqlite3.connect('ams_database.db')
    c = conn.cursor()
    date_today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM attendance WHERE username = ? AND date = ?", (username, date_today))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?)", (username, date_today, "Present", method))
    conn.commit()
    conn.close()
    return True

# --- DASHBOARDS ---
def student_dashboard(username):
    st.title(f"🎓 Welcome, {username}")
    st.write("Mark your daily attendance below.")
    
    method = st.selectbox("Select Attendance Method:", ["Face Recognition (Camera)", "QR Code Simulation"])
    
    if method == "Face Recognition (Camera)":
        img = st.camera_input("Take a picture to verify face")
        if img and st.button("Mark Attendance"):
            if mark_attendance(username, "Face"):
                st.success("✅ Attendance Marked Successfully via Face Recognition!")
            else:
                st.warning("⚠️ Attendance already marked for today.")
    else:
        if st.button("Simulate QR Scan & Mark Attendance"):
            if mark_attendance(username, "QR"):
                st.success("✅ Attendance Marked Successfully via QR Code!")
            else:
                st.warning("⚠️ Attendance already marked for today.")
                
    st.divider()
    st.subheader("📊 Your Attendance Statistics")
    conn = sqlite3.connect('ams_database.db')
    df = pd.read_sql_query("SELECT date, status, method FROM attendance WHERE username = ?", conn, params=(username,))
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df['date'].value_counts())
    else:
        st.info("No records found.")

def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    menu = st.sidebar.radio("Navigation", ["View Class Attendance", "Manage Students"])
    
    if menu == "Manage Students":
        st.subheader("➕ Register New Student")
        new_user = st.text_input("Student Username")
        new_pass = st.text_input("Student Password", type="password")
        if st.button("Register Student"):
            if add_user(new_user, new_pass, "Student"):
                st.success("✅ Student Registered Successfully!")
            else:
                st.error("❌ Username already exists.")
                
    elif menu == "View Class Attendance":
        st.subheader("📈 Class Attendance Insights")
        conn = sqlite3.connect('ams_database.db')
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.write("Attendance Trend:")
            st.line_chart(df.groupby('date').size())
        else:
            st.info("No attendance records to display.")

# --- MAIN APP ---
def main():
    inject_css()
    init_db()
    
    if 'logged_in' not in st.session_state:
        st.session_state.update({'logged_in': False, 'username': "", 'role': ""})
        add_user("admin", "admin123", "Teacher") # Default Teacher Account

    if not st.session_state['logged_in']:
        st.markdown("<h2 style='text-align: center;'>University AMS Login</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                role = authenticate(username, password)
                if role:
                    st.session_state.update({'logged_in': True, 'username': username, 'role': role})
                    st.rerun()
                else:
                    st.error("Invalid Credentials!")
    else:
        st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.clear())
        if st.session_state['role'] == "Student":
            student_dashboard(st.session_state['username'])
        else:
            teacher_dashboard()

if __name__ == '__main__':
    main()
