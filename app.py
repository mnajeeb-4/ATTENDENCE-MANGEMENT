import streamlit as st
import pandas as pd
import os
import time
import hashlib
import qrcode
import cv2
import numpy as np
from PIL import Image
import plotly.express as px

# --- ULTRA MODERN CSS & HTML INTERFACE ---
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    /* Glassmorphism Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main-header {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 20px;
        color: #1f2937;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .main-header h1 { font-weight: 700; margin: 0; letter-spacing: -0.5px; }
    .main-header p { color: #4b5563; font-weight: 400; margin-top: 5px; }
    
    .stButton > button {
        width: 100%;
        background: #1e3a8a;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        background: #233876;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(5px);
        padding: 30px;
        border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.5);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA PRIVACY & UTILITY FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_data():
    os.makedirs("data", exist_ok=True)
    os.makedirs("qr_codes", exist_ok=True)
    
    # Creating Empty files if not exist
    if not os.path.exists("data/users.csv"):
        df = pd.DataFrame(columns=["username", "password_hash", "role", "name", "email", "phone", "created_by"])
        df.to_csv("data/users.csv", index=False)
        
    if not os.path.exists("data/attendance.csv"):
        df = pd.DataFrame(columns=["username", "date", "time", "method", "status"])
        df.to_csv("data/attendance.csv", index=False)
    
    # Auto-create Head Teacher (Najeeb) on first run
    users = load_users()
    if "najeeb" not in users["username"].values:
        new_row = pd.DataFrame([[
            "najeeb", hash_password("inajeeb123"), "HeadTeacher", 
            "Mr. Najeeb", "najeeb@university.edu", "+92 300 0000000", "system"
        ]], columns=["username", "password_hash", "role", "name", "email", "phone", "created_by"])
        users = pd.concat([users, new_row], ignore_index=True)
        save_users(users)

def load_users():
    return pd.read_csv("data/users.csv")

def save_users(df):
    df.to_csv("data/users.csv", index=False)

def load_attendance():
    return pd.read_csv("data/attendance.csv")

def save_attendance(df):
    df.to_csv("data/attendance.csv", index=False)

# --- QR CODE GENERATION ---
def generate_qr(username):
    img = qrcode.make(username)
    path = f"qr_codes/{username}.png"
    img.save(path)
    return path

# --- CLOUD VERSION: QR CODE ATTENDANCE ---
def mark_attendance_qr(qr_upload, username):
    try:
        img = Image.open(qr_upload)
        img_np = np.array(img)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_np)
        
        if data and data.strip() == username.strip():
            now = time.localtime()
            date = time.strftime("%Y-%m-%d", now)
            t = time.strftime("%H:%M:%S", now)
            
            df = load_attendance()
            new_record = pd.DataFrame([[username, date, t, "QR Code (Cloud)", "Present"]], 
                                     columns=["username", "date", "time", "method", "status"])
            df = pd.concat([df, new_record], ignore_index=True)
            save_attendance(df)
            return True, "Attendance Marked Successfully via QR Code!"
        else:
            return False, "Invalid QR Code for this student!"
    except Exception as e:
        return False, f"Error processing QR Code: {str(e)}"

# --- STREAMLIT APP LOGIC ---
def main():
    load_css()
    init_data()
    
    # Sidebar Menu
    st.sidebar.title("📚 AMS Portal")
    
    if "logged_in" not in st.session_state:
        menu = st.sidebar.selectbox("Select Option", ["Login", "Register Student"])
    else:
        menu = st.sidebar.selectbox("Select Option", ["Dashboard", "Logout"])
    
    # ---------------- LOGIN ----------------
    if menu == "Login":
        st.markdown('<div class="main-header"><h1>🎓 Secure Login</h1></div>', unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("login_form"):
                    st.markdown('<div class="card"><h3 style="color:#1f2937;">🔐 Welcome Back</h3>', unsafe_allow_html=True)
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    login_btn = st.form_submit_button("Login")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if login_btn:
                        users = load_users()
                        hashed_input = hash_password(password)
                        user = users[(users["username"] == username) & (users["password_hash"] == hashed_input)]
                        
                        if not user.empty:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["role"] = user.iloc[0]['role']
                            st.session_state["user_name"] = user.iloc[0]['name']
                            st.success(f"Welcome back, {user.iloc[0]['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password!")

    # ---------------- STUDENT SELF REGISTRATION ----------------
    elif menu == "Register Student":
        st.markdown('<div class="main-header"><h1>📝 Student Registration</h1></div>', unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("student_reg"):
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Register Yourself")
                    name = st.text_input("Full Name")
                    username = st.text_input("Desired Username")
                    phone = st.text_input("Phone Number")
                    email = st.text_input("Email")
                    password = st.text_input("Create Password", type="password")
                    submit_reg = st.form_submit_button("Register as Student")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if submit_reg:
                        users = load_users()
                        if username in users["username"].values:
                            st.error("Username already taken! Please choose another.")
                        elif not username or not password:
                            st.error("Username and Password are required.")
                        else:
                            new_row = pd.DataFrame([[
                                username, hash_password(password), "Student", 
                                name, email, phone, "self"
                            ]], columns=["username", "password_hash", "role", "name", "email", "phone", "created_by"])
                            
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users)
                            generate_qr(username)
                            st.success(f"Registration Successful for {name}! You can now login.")

    # ---------------- DASHBOARD (ROLE BASED) ----------------
    elif menu == "Dashboard" and "logged_in" in st.session_state:
        role = st.session_state["role"]
        
        # --- HEAD TEACHER DASHBOARD (NAJEEB) ---
        if role == "HeadTeacher":
            st.markdown(f'<div class="main-header"><h1>👑 Head Teacher Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            if st.sidebar.button("🚪 Logout"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
            
            tab1, tab2 = st.tabs(["➕ Add New Teacher", "📋 All Users Data"])
            
            with tab1:
                with st.form("add_teacher"):
                    st.subheader("Register a New Teacher")
                    t_name = st.text_input("Teacher Full Name")
                    t_username = st.text_input("Teacher Username")
                    t_pass = st.text_input("Teacher Password", type="password")
                    t_email = st.text_input("Teacher Email")
                    t_phone = st.text_input("Teacher Phone")
                    
                    if st.form_submit_button("Add Teacher"):
                        users = load_users()
                        if t_username in users["username"].values:
                            st.error("Username already exists!")
                        else:
                            new_row = pd.DataFrame([[
                                t_username, hash_password(t_pass), "Teacher", 
                                t_name, t_email, t_phone, "najeeb"
                            ]], columns=["username", "password_hash", "role", "name", "email", "phone", "created_by"])
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users)
                            generate_qr(t_username)
                            st.success(f"Teacher {t_name} added successfully!")
            
            with tab2:
                st.dataframe(load_users(), use_container_width=True)

        # --- TEACHER DASHBOARD ---
        elif role == "Teacher":
            st.markdown(f'<div class="main-header"><h1>🧑‍🏫 Teacher Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            if st.sidebar.button("🚪 Logout"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
                
            tab1, tab2 = st.tabs(["📊 Analytics", "📋 Attendance Records"])
            
            with tab1:
                st.subheader("Class Attendance Analytics")
                df = load_attendance()
                if df.empty:
                    st.info("No attendance records found yet.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.pie(df, names='username', title='Attendance Distribution', hole=0.4, color_discrete_sequence=px.colors.sequential.Bluyl)
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        fig_bar = px.bar(df.groupby('username').count().reset_index(), x='username', y='date', title='Total Count', color='username', text_auto=True)
                        st.plotly_chart(fig_bar, use_container_width=True)
            
            with tab2:
                st.subheader("All Students Attendance Records")
                st.dataframe(load_attendance(), use_container_width=True)

        # --- STUDENT DASHBOARD ---
        elif role == "Student":
            username = st.session_state["username"]
            st.markdown(f'<div class="main-header"><h1>🧑‍🎓 Student Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            if st.sidebar.button("🚪 Logout"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
                
            tab1, tab2, tab3 = st.tabs(["Mark Attendance", "My Stats", "My QR"])
            
            with tab1:
                st.subheader("📸 Mark Attendance via QR Code")
                qr_img = st.file_uploader("Upload QR Code", type=['png', 'jpg', 'jpeg'])
                if qr_img is not None and st.button("✅ Mark Attendance"):
                    status, msg = mark_attendance_qr(qr_img, username)
                    if status: st.success(msg) 
                    else: st.error(msg)
            
            with tab2:
                st.subheader("📈 My Performance")
                df = load_attendance()
                my_data = df[df["username"] == username]
                if my_data.empty:
                    st.info("No records yet.")
                else:
                    fig = px.line(my_data, x='date', y='time', markers=True, title=f'Attendance History')
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric(label="Total Present Days", value=len(my_data))
            
            with tab3:
                st.subheader("🆔 My ID QR Code")
                qr_path = f"qr_codes/{username}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="Scan to Mark Attendance", width=200)
                    with open(qr_path, "rb") as f:
                        st.download_button("⬇️ Download QR", f, file_name=f"{username}_qr.png")
                else:
                    st.warning("QR Code not found.")

    # ---------------- LOGOUT ----------------
    elif menu == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
