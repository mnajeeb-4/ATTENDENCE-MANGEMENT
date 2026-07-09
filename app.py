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
import smtplib
import random

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
    .otp-box {
        background: #fef08a;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ca8a04;
        color: #854d0e;
        font-weight: 600;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA PRIVACY & UTILITY FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_data():
    os.makedirs("data", exist_ok=True)
    os.makedirs("qr_codes", exist_ok=True)
    
    # Creating Empty files if not exist (NO HARDCODED USERS created automatically now)
    if not os.path.exists("data/users.csv"):
        df = pd.DataFrame(columns=["username", "password_hash", "role", "name", "email", "phone"])
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

# --- REAL OTP EMAIL SERVICE ---
def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(receiver_email, otp):
    try:
        # Accessing secrets safely
        sender_email = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        
        subject = "Attendance System: Teacher Registration OTP"
        body = f"Dear Teacher,\n\nYour OTP for registration is: {otp}\n\nDo not share this OTP with anyone.\n\nRegards,\nAMS Team"
        message = f"Subject: {subject}\n\n{body}"
        
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        return True
    except Exception as e:
        # Fallback: Log error but don't crash
        print(f"Email Error: {e}")
        return False

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
    menu = st.sidebar.selectbox("Select Option", ["Teacher Login", "Register Teacher", "Student Dashboard"])
    
    # ---------------- TEACHER LOGIN ----------------
    if menu == "Teacher Login":
        st.markdown('<div class="main-header"><h1>🎓 Teacher Login</h1><p>Secure Cloud Authentication</p></div>', unsafe_allow_html=True)
        
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
                        user = users[(users["username"] == username) & (users["password_hash"] == hashed_input) & (users["role"] == "Teacher")]
                        
                        if not user.empty:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["role"] = "Teacher"
                            st.session_state["user_name"] = user.iloc[0]['name']
                            st.success(f"Welcome back, {user.iloc[0]['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid Credentials or Account not registered!")

    # ---------------- TEACHER SELF-REGISTRATION WITH OTP ----------------
    elif menu == "Register Teacher":
        st.markdown('<div class="main-header"><h1>📝 Teacher Registration</h1><p>Verify via Email OTP</p></div>', unsafe_allow_html=True)
        
        # Step 1: Collect Data
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("reg_form"):
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Register as Teacher")
                    name = st.text_input("Full Name", value="Mr. Najeeb")
                    username = st.text_input("Desired Username", value="najeeb")
                    phone = st.text_input("Phone Number", placeholder="+92 300 1234567")
                    email = st.text_input("Email (For OTP)", placeholder="teacher@gmail.com")
                    password = st.text_input("Password", type="password", value="inajeeb123")
                    
                    submit_reg = st.form_submit_button("Proceed to OTP Verification")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if submit_reg:
                        users = load_users()
                        if username in users["username"].values:
                            st.error("Username already taken! Please choose another.")
                        elif not email:
                            st.error("Email is required to receive OTP.")
                        else:
                            # Generate OTP and store in session
                            otp_code = generate_otp()
                            st.session_state["pending_otp"] = otp_code
                            st.session_state["pending_user"] = {
                                "name": name, "username": username, "email": email, 
                                "phone": phone, "password": hash_password(password)
                            }
                            
                            # Try sending real email
                            email_sent = send_otp_email(email, otp_code)
                            
                            if email_sent:
                                st.success(f"OTP sent successfully to {email}! Check your inbox.")
                            else:
                                st.warning("⚠️ Email service is currently offline. For demo purpose, OTP is shown below:")
                                st.markdown(f'<div class="otp-box">🔑 Your One-Time Password (OTP) is: {otp_code}</div>', unsafe_allow_html=True)
                            
                            st.session_state["step"] = "verify_otp"
                            st.rerun()

        # Step 2: Verify OTP
        if "step" in st.session_state and st.session_state["step"] == "verify_otp":
            st.markdown("### ✅ Verify OTP")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                otp_input = st.text_input("Enter the 6-digit OTP sent to your email", max_chars=6)
                if st.button("Verify OTP & Create Account"):
                    if otp_input and int(otp_input) == st.session_state["pending_otp"]:
                        # Save the user to CSV
                        users = load_users()
                        new_user = st.session_state["pending_user"]
                        new_row = pd.DataFrame([[
                            new_user["username"], new_user["password"], "Teacher", 
                            new_user["name"], new_user["email"], new_user["phone"]
                        ]], columns=["username", "password_hash", "role", "name", "email", "phone"])
                        
                        users = pd.concat([users, new_row], ignore_index=True)
                        save_users(users)
                        generate_qr(new_user["username"])
                        
                        st.success(f"Account created successfully for {new_user['name']}! You can now login.")
                        # Cleanup session
                        del st.session_state["step"]
                        del st.session_state["pending_otp"]
                        del st.session_state["pending_user"]
                        st.rerun()
                    else:
                        st.error("Incorrect OTP. Please try again.")

    # ---------------- TEACHER DASHBOARD (After Login) ----------------
    if "logged_in" in st.session_state and st.session_state["role"] == "Teacher":
        st.markdown(f'<div class="main-header"><h1>👨‍🏫 Teacher Dashboard</h1><p>Welcome, {st.session_state["user_name"]}</p></div>', unsafe_allow_html=True)
        
        # Custom Sidebar for Logout
        if st.sidebar.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
        tab1, tab2, tab3 = st.tabs(["➕ Add Student", "📊 Analytics", "📋 Records"])
        
        with tab1:
            with st.form("add_student"):
                st.subheader("Register a New Student")
                new_name = st.text_input("Full Name")
                new_username = st.text_input("Username (Unique ID)")
                new_pass = st.text_input("Create a Password for Student", type="password")
                if st.form_submit_button("Add Student"):
                    users = load_users()
                    if new_username in users["username"].values:
                        st.error("Username already exists!")
                    else:
                        new_row = pd.DataFrame([[
                            new_username, hash_password(new_pass), "Student", 
                            new_name, "N/A", "N/A"
                        ]], columns=["username", "password_hash", "role", "name", "email", "phone"])
                        users = pd.concat([users, new_row], ignore_index=True)
                        save_users(users)
                        generate_qr(new_username)
                        st.success(f"Student {new_name} added successfully! ID Card QR generated.")
        
        with tab2:
            st.subheader("📊 Class Attendance Analytics")
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
        
        with tab3:
            st.subheader("📋 All Students Attendance Records")
            st.dataframe(load_attendance(), use_container_width=True)

    # ---------------- STUDENT DASHBOARD ----------------
    elif menu == "Student Dashboard":
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("student_login_form"):
                    st.markdown('<div class="card"><h3 style="color:#1f2937;">🧑‍🎓 Student Login</h3>', unsafe_allow_html=True)
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    login_btn = st.form_submit_button("Login")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if login_btn:
                        users = load_users()
                        hashed_input = hash_password(password)
                        user = users[(users["username"] == username) & (users["password_hash"] == hashed_input) & (users["role"] == "Student")]
                        
                        if not user.empty:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.session_state["role"] = "Student"
                            st.rerun()
                        else:
                            st.error("Invalid Student Credentials!")

        if "logged_in" in st.session_state and st.session_state["role"] == "Student":
            username = st.session_state["username"]
            st.markdown(f'<div class="main-header"><h1>🧑‍🎓 Student Dashboard</h1><p>Welcome, {username}</p></div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Mark Attendance", "My Stats", "My QR"])
            
            with tab1:
                st.subheader("📸 Mark Attendance via QR Code")
                st.info("Upload the QR code image generated by your Teacher.")
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
                st.subheader("🆔 My QR Code")
                qr_path = f"qr_codes/{username}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, caption="Scan to Mark Attendance", width=200)
                    with open(qr_path, "rb") as f:
                        st.download_button("⬇️ Download QR", f, file_name=f"{username}_qr.png")
                else:
                    st.warning("QR not generated yet. Contact your teacher.")

if __name__ == "__main__":
    main()
