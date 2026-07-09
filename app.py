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
from datetime import datetime, timedelta

# --- ULTRA MODERN CSS & HTML INTERFACE ---
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
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
    /* Styling the dataframe grid */
    .stDataFrame {
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA PRIVACY & UTILITY FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_csv_structure():
    os.makedirs("data", exist_ok=True)
    os.makedirs("qr_codes", exist_ok=True)
    
    # Users CSV
    user_cols = ["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"]
    if not os.path.exists("data/users.csv"):
        pd.DataFrame(columns=user_cols).to_csv("data/users.csv", index=False)
    else:
        df = pd.read_csv("data/users.csv")
        for col in user_cols:
            if col not in df.columns:
                df[col] = "" 
        df.to_csv("data/users.csv", index=False)
        
    # Attendance CSV
    att_cols = ["username", "date", "checkin_time", "checkout_time", "status", "method"]
    if not os.path.exists("data/attendance.csv"):
        pd.DataFrame(columns=att_cols).to_csv("data/attendance.csv", index=False)
    else:
        df = pd.read_csv("data/attendance.csv")
        for col in att_cols:
            if col not in df.columns:
                df[col] = ""
        df.to_csv("data/attendance.csv", index=False)

    # Auto-create Head Teacher Najeeb
    users = load_users()
    if "najeeb" not in users["username"].values:
        new_row = pd.DataFrame([[
            "najeeb", hash_password("inajeeb123"), "HeadTeacher", 
            "Mr. Najeeb", "najeeb@university.edu", "+92 300 0000000", "Admin", "All", "system"
        ]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
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

# --- CLOUD VERSION: QR CODE ATTENDANCE (CHECK-IN, CHECK-OUT, LEAVE) ---
def mark_attendance_qr(qr_upload, username, action):
    try:
        img = Image.open(qr_upload)
        img_np = np.array(img)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_np)
        
        if data and data.strip() == username.strip():
            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            df = load_attendance()
            today_record = df[(df["username"] == username) & (df["date"] == date)]
            
            if action == "Check In":
                if not today_record.empty and today_record.iloc[0]["checkin_time"] != "":
                    return False, "You have already Checked In today!"
                new_record = pd.DataFrame([[username, date, time_str, "", "Present", "QR Code"]], 
                                         columns=["username", "date", "checkin_time", "checkout_time", "status", "method"])
                df = pd.concat([df, new_record], ignore_index=True)
                save_attendance(df)
                return True, f"✅ Check In Successful at {time_str}!"

            elif action == "Check Out":
                if today_record.empty or today_record.iloc[0]["checkin_time"] == "":
                    return False, "You haven't Checked In today!"
                if today_record.iloc[0]["checkout_time"] != "":
                    return False, "You have already Checked Out today!"
                
                # Update the Check-Out time
                df.loc[(df["username"] == username) & (df["date"] == date), "checkout_time"] = time_str
                save_attendance(df)
                return True, f"✅ Check Out Successful at {time_str}!"

            elif action == "Mark Leave":
                if not today_record.empty:
                    return False, "Attendance already marked for today!"
                new_record = pd.DataFrame([[username, date, time_str, time_str, "Leave", "QR Code"]], 
                                         columns=["username", "date", "checkin_time", "checkout_time", "status", "method"])
                df = pd.concat([df, new_record], ignore_index=True)
                save_attendance(df)
                return True, "✅ Leave Marked Successfully!"
                
        else:
            return False, "Invalid QR Code for this user!"
    except Exception as e:
        return False, f"Error processing QR Code: {str(e)}"

# --- CALENDAR GRID VIEW GENERATOR ---
def get_attendance_grid(usernames, days=7):
    """Generates a grid similar to the screenshot (Rows=Users, Cols=Dates)"""
    df_att = load_attendance()
    today = datetime.now().date()
    date_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days-1, -1, -1)]
    
    grid_data = []
    for user in usernames:
        row = {"username": user}
        for d in date_list:
            record = df_att[(df_att["username"] == user) & (df_att["date"] == d)]
            if record.empty:
                row[d] = "A" # Absent
            else:
                r = record.iloc[0]
                if r["status"] == "Leave":
                    row[d] = "L"
                else:
                    checkin = r["checkin_time"] if pd.notna(r["checkin_time"]) else ""
                    checkout = r["checkout_time"] if pd.notna(r["checkout_time"]) else ""
                    if checkout:
                        row[d] = f"P ({checkin}-{checkout})"
                    else:
                        row[d] = f"P ({checkin})"
        grid_data.append(row)
    
    grid_df = pd.DataFrame(grid_data)
    return grid_df, date_list

# --- STREAMLIT APP LOGIC ---
def main():
    load_css()
    ensure_csv_structure()
    
    # Sidebar Menu
    st.sidebar.title("📚 AMS Portal")
    
    if "logged_in" not in st.session_state:
        # Only Students can Register publicly. Teachers are added by Najeeb.
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
                            st.session_state["class_name"] = user.iloc[0]['class_name']
                            st.success(f"Welcome back, {user.iloc[0]['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password!")

    # ---------------- STUDENT SELF REGISTRATION (ONLY) ----------------
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
                    email = st.text_input("Email")
                    phone = st.text_input("Phone Number")
                    class_name = st.text_input("Your Class/Batch (e.g. CS-2026)")
                    password = st.text_input("Create Password", type="password")
                    submit_reg = st.form_submit_button("Register as Student")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if submit_reg:
                        users = load_users()
                        if username in users["username"].values:
                            st.error("Username already taken!")
                        elif not username or not password:
                            st.error("Username and Password are required.")
                        else:
                            new_row = pd.DataFrame([[
                                username, hash_password(password), "Student", 
                                name, email, phone, "Student", class_name, "self"
                            ]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users)
                            generate_qr(username)
                            st.success(f"Registration Successful for {name}! You can now login.")

    # ---------------- DASHBOARD (ROLE BASED) ----------------
    elif menu == "Dashboard" and "logged_in" in st.session_state:
        role = st.session_state["role"]
        current_username = st.session_state["username"]
        current_class = st.session_state["class_name"]
        
        if st.sidebar.button("🚪 Logout"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
            
        # --- HEAD TEACHER DASHBOARD (NAJEEB) ---
        if role == "HeadTeacher":
            st.markdown(f'<div class="main-header"><h1>👑 Head Teacher Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["➕ Add New Teacher", "📊 All System Attendance"])
            
            with tab1:
                with st.form("add_teacher"):
                    st.subheader("Register a New Teacher")
                    t_name = st.text_input("Teacher Full Name")
                    t_username = st.text_input("Teacher Username")
                    t_pass = st.text_input("Teacher Password", type="password")
                    t_email = st.text_input("Teacher Email")
                    t_phone = st.text_input("Teacher Phone")
                    t_prof = st.text_input("Teacher Profession")
                    t_class = st.text_input("Teacher's Class/Batch")
                    
                    if st.form_submit_button("Add Teacher"):
                        users = load_users()
                        if t_username in users["username"].values:
                            st.error("Username already exists!")
                        else:
                            new_row = pd.DataFrame([[
                                t_username, hash_password(t_pass), "Teacher", 
                                t_name, t_email, t_phone, t_prof, t_class, "najeeb"
                            ]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users)
                            generate_qr(t_username)
                            
                            st.success(f"Teacher {t_name} added successfully!")
                            
                            # NEW: Immediately show QR Code to Head Teacher
                            qr_path = f"qr_codes/{t_username}.png"
                            st.image(qr_path, caption=f"{t_name}'s QR Code", width=200)
                            with open(qr_path, "rb") as f:
                                st.download_button("⬇️ Download Teacher QR", f, file_name=f"{t_username}_qr.png")
            
            with tab2:
                all_users = load_users()
                all_usernames = all_users["username"].tolist()
                grid_df, date_cols = get_attendance_grid(all_usernames, days=30)
                st.subheader("Attendance Calendar (Last 30 Days)")
                st.dataframe(grid_df.style.map(lambda x: 'background-color: #d4edda' if 'P' in str(x) else ('background-color: #f8d7da' if 'A' == str(x) else ('background-color: #fff3cd' if 'L' == str(x) else '')), subset=date_cols), use_container_width=True)

        # --- TEACHER DASHBOARD ---
        elif role == "Teacher":
            st.markdown(f'<div class="main-header"><h1>🧑‍🏫 Teacher Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            users_df = load_users()
            class_students = users_df[(users_df["class_name"] == current_class) & (users_df["role"] == "Student")]["username"].tolist()
            view_usernames = [current_username] + class_students
            
            # NEW: Added the 4th tab for "My QR"
            tab1, tab2, tab3, tab4 = st.tabs(["📸 Mark Attendance", "📊 Class Attendance (Grid)", "📋 Details", "🆔 My QR"])
            
            with tab1:
                st.subheader("Mark Your Attendance via QR Code")
                st.info("💡 Download your QR from the 'My QR' tab, then upload it here to mark attendance.")
                action = st.radio("Select Action:", ["Check In", "Check Out", "Mark Leave"], horizontal=True)
                qr_img = st.file_uploader("Upload Your QR Code", type=['png', 'jpg', 'jpeg'])
                if qr_img is not None and st.button("✅ Submit Attendance"):
                    status, msg = mark_attendance_qr(qr_img, current_username, action)
                    if status: st.success(msg) 
                    else: st.error(msg)
            
            with tab2:
                st.subheader(f"Grid View: My Class ({current_class})")
                grid_df, date_cols = get_attendance_grid(view_usernames, days=30)
                st.dataframe(grid_df.style.map(lambda x: 'background-color: #d4edda' if 'P' in str(x) else ('background-color: #f8d7da' if 'A' == str(x) else ('background-color: #fff3cd' if 'L' == str(x) else '')), subset=date_cols), use_container_width=True)
            
            with tab3:
                st.subheader("Detailed Attendance Records")
                df_att = load_attendance()
                st.dataframe(df_att[df_att["username"].isin(view_usernames)], use_container_width=True)

            # NEW: My QR Tab for Teachers
            with tab4:
                st.subheader("🆔 My ID QR Code")
                qr_path = f"qr_codes/{current_username}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="Scan to Mark Attendance", width=200)
                    with open(qr_path, "rb") as f:
                        st.download_button("⬇️ Download My QR", f, file_name=f"{current_username}_qr.png")
                else:
                    st.warning("QR Code not found. Please contact Head Teacher.")

        # --- STUDENT DASHBOARD ---
        elif role == "Student":
            st.markdown(f'<div class="main-header"><h1>🧑‍🎓 Student Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Mark Attendance", "My Statistics", "My QR"])
            
            with tab1:
                st.subheader("Mark Attendance via QR Code")
                st.info("💡 Download your QR from the 'My QR' tab, then upload it here to mark attendance.")
                action = st.radio("Select Action:", ["Check In", "Check Out", "Mark Leave"], horizontal=True)
                qr_img = st.file_uploader("Upload QR Code", type=['png', 'jpg', 'jpeg'])
                if qr_img is not None and st.button("✅ Submit Attendance"):
                    status, msg = mark_attendance_qr(qr_img, current_username, action)
                    if status: st.success(msg) 
                    else: st.error(msg)
            
            with tab2:
                st.subheader("📈 My Performance (Grid View)")
                grid_df, date_cols = get_attendance_grid([current_username], days=30)
                st.dataframe(grid_df.style.map(lambda x: 'background-color: #d4edda' if 'P' in str(x) else ('background-color: #f8d7da' if 'A' == str(x) else ('background-color: #fff3cd' if 'L' == str(x) else '')), subset=date_cols), use_container_width=True)
                
                st.subheader("Detailed Check-In/Out Logs")
                df = load_attendance()
                my_data = df[df["username"] == current_username]
                st.dataframe(my_data, use_container_width=True)
            
            with tab3:
                st.subheader("🆔 My ID QR Code")
                qr_path = f"qr_codes/{current_username}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="Scan to Mark Attendance", width=200)
                    with open(qr_path, "rb") as f:
                        st.download_button("⬇️ Download QR", f, file_name=f"{current_username}_qr.png")
                else:
                    st.warning("QR Code not found. Contact your teacher.")

    # ---------------- LOGOUT ----------------
    elif menu == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
