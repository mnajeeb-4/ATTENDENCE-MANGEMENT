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

# --- MODERN CSS & HTML INTERFACE ---
def load_css():
    st.markdown("""
    <style>
    /* Modern Professional CSS */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .main-header {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button {
        width: 100%;
        background-color: #4b6cb7;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background-color: #182848;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA PRIVACY & UTILITY FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_data():
    os.makedirs("data", exist_ok=True)
    os.makedirs("qr_codes", exist_ok=True)
    
    if not os.path.exists("data/users.csv"):
        df = pd.DataFrame(columns=["username", "password_hash", "role", "name"])
        df.loc[0] = ["teacher", hash_password("teacher123"), "Teacher", "Mr. John Doe"]
        df.loc[1] = ["student1", hash_password("student123"), "Student", "Alice Smith"]
        df.to_csv("data/users.csv", index=False)
        
    if not os.path.exists("data/attendance.csv"):
        df = pd.DataFrame(columns=["username", "date", "time", "method", "status"])
        df.to_csv("data/attendance.csv", index=False)

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

# --- CLOUD VERSION: QR CODE ATTENDANCE (Face Recognition hata diya gaya) ---
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
    
    st.sidebar.title("📚 Attendance System (Cloud)")
    menu = st.sidebar.selectbox("Select Login Role", ["Login", "Teacher Dashboard", "Student Dashboard"])
    
    if menu == "Login":
        st.markdown('<div class="main-header"><h1>🎓 Attendance Management System</h1><p>Secure Cloud Deployment | Use QR Codes</p></div>', unsafe_allow_html=True)
        
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                with st.form("login_form"):
                    st.markdown("### 🔐 Secure Login")
                    role = st.selectbox("Select Role", ["Teacher", "Student"])
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    login_btn = st.form_submit_button("Login")
                    
                    if login_btn:
                        users = load_users()
                        hashed_input = hash_password(password)
                        user = users[(users["username"] == username) & (users["password_hash"] == hashed_input) & (users["role"] == role)]
                        
                        if not user.empty:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["role"] = role
                            st.success(f"Welcome {user.iloc[0]['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid Credentials or Role Mismatch!")

    elif menu == "Teacher Dashboard":
        if "logged_in" in st.session_state and st.session_state["role"] == "Teacher":
            st.markdown('<div class="main-header"><h1>👨‍🏫 Teacher Dashboard</h1><p>Manage Students & View Analytics</p></div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Add Student", "View Analytics", "All Records"])
            
            with tab1:
                with st.form("add_student"):
                    st.subheader("Add New Student")
                    new_name = st.text_input("Full Name")
                    new_username = st.text_input("Username (Unique ID)")
                    new_pass = st.text_input("Temp Password", type="password")
                    if st.form_submit_button("Add Student"):
                        users = load_users()
                        if new_username in users["username"].values:
                            st.error("Username already exists!")
                        else:
                            new_row = pd.DataFrame([[new_username, hash_password(new_pass), "Student", new_name]], 
                                                  columns=["username", "password_hash", "role", "name"])
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users)
                            generate_qr(new_username)
                            st.success(f"Student {new_name} added successfully! QR generated.")
            
            with tab2:
                st.subheader("📊 Attendance Statistics")
                df = load_attendance()
                if df.empty:
                    st.warning("No attendance records yet.")
                else:
                    fig = px.pie(df, names='username', title='Attendance Distribution by Student', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig_bar = px.bar(df.groupby('username').count().reset_index(), x='username', y='date', title='Total Attendance Count')
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            with tab3:
                st.subheader("📋 All Attendance Records")
                df = load_attendance()
                st.dataframe(df, use_container_width=True)
                
        else:
            st.error("Please Login as Teacher first.")
            
    elif menu == "Student Dashboard":
        if "logged_in" in st.session_state and st.session_state["role"] == "Student":
            username = st.session_state["username"]
            st.markdown(f'<div class="main-header"><h1>🧑‍🎓 Student Dashboard</h1><p>Welcome, {username}!</p></div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Mark Attendance", "My Stats", "QR Code"])
            
            with tab1:
                st.subheader("Mark Attendance")
                st.info("Note: Cloud version supports QR Code only. Face Recognition is available in Local Version.")
                
                # Face Recognition button removed entirely for cloud to avoid Camera Crash
                
                qr_img = st.file_uploader("Upload Your QR Code Image", type=['png', 'jpg', 'jpeg'])
                if qr_img is not None and st.button("✅ Mark Attendance via QR"):
                    status, msg = mark_attendance_qr(qr_img, username)
                    if status:
                        st.success(msg)
                    else:
                        st.error(msg)
                            
            with tab2:
                st.subheader("📈 My Attendance Statistics")
                df = load_attendance()
                my_data = df[df["username"] == username]
                if my_data.empty:
                    st.info("No attendance records found for you yet.")
                else:
                    fig = px.line(my_data, x='date', y='time', title=f'Attendance History for {username}', markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric(label="Total Attendance", value=len(my_data))
            
            with tab3:
                st.subheader("My ID QR Code")
                qr_path = f"qr_codes/{username}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="Your Attendance QR Code", width=200)
                    with open(qr_path, "rb") as f:
                        st.download_button("Download QR Code", f, file_name=f"{username}_qr.png")
                else:
                    st.warning("QR Code not generated. Contact Teacher.")
                
        else:
            st.error("Please Login as Student first.")

if __name__ == "__main__":
    main()
