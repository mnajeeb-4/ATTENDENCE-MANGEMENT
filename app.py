import streamlit as st
import pandas as pd
import os
import hashlib
import qrcode
import cv2
import numpy as np
from PIL import Image
import plotly.express as px
from datetime import datetime, timedelta

# --- MODERN CSS INTERFACE (PROFESSIONAL GLASSMORPHISM) ---
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .main-header {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 20px;
        color: #1f2937; text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .main-header h1 { font-weight: 700; margin: 0; letter-spacing: -0.5px; }
    .stButton > button {
        width: 100%; background: #1e3a8a; color: white; border-radius: 12px;
        border: none; padding: 12px 24px; font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: translateY(-2px); background: #233876; }
    .card {
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(5px);
        padding: 30px; border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.5); margin-bottom: 20px;
    }
    .grid-cell-red { background-color: #f8d7da !important; } /* Absent */
    .grid-cell-green { background-color: #d4edda !important; } /* Present */
    .grid-cell-yellow { background-color: #fff3cd !important; } /* Leave */
    </style>
    """, unsafe_allow_html=True)

# --- DATA PRIVACY & UTILITY FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_csv_structure():
    os.makedirs("data", exist_ok=True); os.makedirs("qr_codes", exist_ok=True)
    # Users File
    user_cols = ["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"]
    if not os.path.exists("data/users.csv"):
        pd.DataFrame(columns=user_cols).to_csv("data/users.csv", index=False)
    
    # Attendance File
    att_cols = ["username", "date", "checkin_time", "checkout_time", "status", "method"]
    if not os.path.exists("data/attendance.csv"):
        pd.DataFrame(columns=att_cols).to_csv("data/attendance.csv", index=False)

    # Auto-create Head Teacher Najeeb
    users = load_users()
    if "najeeb" not in users["username"].values:
        new_row = pd.DataFrame([[
            "najeeb", hash_password("inajeeb123"), "HeadTeacher", 
            "Mr. Najeeb", "najeeb@university.edu", "+92 300 0000000", "Admin", "All", "system"
        ]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
        users = pd.concat([users, new_row], ignore_index=True)
        save_users(users)

def load_users(): return pd.read_csv("data/users.csv")
def save_users(df): df.to_csv("data/users.csv", index=False)
def load_attendance(): return pd.read_csv("data/attendance.csv")
def save_attendance(df): df.to_csv("data/attendance.csv", index=False)

# --- QR CODE GENERATION ---
def generate_qr(username):
    img = qrcode.make(username)
    path = f"qr_codes/{username}.png"
    img.save(path); return path

# --- MARK ATTENDANCE (QR + PASSWORD SECURITY) ---
def mark_attendance_qr(qr_upload, username, password, action):
    try:
        # 1. Verify Password
        users = load_users()
        user = users[users["username"] == username]
        if user.empty or user.iloc[0]["password_hash"] != hash_password(password):
            return False, "❌ Incorrect Login Password!"

        # 2. QR Scan
        img = Image.open(qr_upload)
        img_np = np.array(img)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img_np)
        
        if data and data.strip() == username.strip():
            now = datetime.now(); date = now.strftime("%Y-%m-%d"); time_str = now.strftime("%H:%M:%S")
            df = load_attendance()
            today_record = df[(df["username"] == username) & (df["date"] == date)]
            
            if action == "Check In":
                if not today_record.empty and today_record.iloc[0]["checkin_time"] != "":
                    return False, "You have already Checked In today!"
                new_record = pd.DataFrame([[username, date, time_str, "", "Present", "QR Code"]], columns=["username", "date", "checkin_time", "checkout_time", "status", "method"])
                df = pd.concat([df, new_record], ignore_index=True)
                save_attendance(df)
                return True, f"✅ Check In Successful at {time_str}!"

            elif action == "Check Out":
                if today_record.empty or today_record.iloc[0]["checkin_time"] == "":
                    return False, "You haven't Checked In today!"
                if today_record.iloc[0]["checkout_time"] != "":
                    return False, "You have already Checked Out today!"
                df.loc[(df["username"] == username) & (df["date"] == date), "checkout_time"] = time_str
                save_attendance(df)
                return True, f"✅ Check Out Successful at {time_str}!"

            elif action == "Mark Leave":
                if not today_record.empty: return False, "Attendance already marked!"
                new_record = pd.DataFrame([[username, date, time_str, time_str, "Leave", "QR Code"]], columns=["username", "date", "checkin_time", "checkout_time", "status", "method"])
                df = pd.concat([df, new_record], ignore_index=True)
                save_attendance(df)
                return True, "✅ Leave Marked Successfully!"
        return False, "Invalid QR Code for this user!"
    except Exception as e:
        return False, f"System Error: {str(e)}"

# --- GRID VIEW GENERATOR ---
def get_attendance_grid(usernames, days=30):
    df_att = load_attendance()
    today = datetime.now().date()
    date_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days-1, -1, -1)]
    grid_data = []
    for user in usernames:
        row = {"username": user}
        for d in date_list:
            rec = df_att[(df_att["username"] == user) & (df_att["date"] == d)]
            if rec.empty: row[d] = "A"
            else:
                r = rec.iloc[0]
                if r["status"] == "Leave": row[d] = "L"
                else:
                    ci = r["checkin_time"] if pd.notna(r["checkin_time"]) else ""
                    co = r["checkout_time"] if pd.notna(r["checkout_time"]) else ""
                    row[d] = f"P ({ci}-{co})" if co else f"P ({ci})"
        grid_data.append(row)
    return pd.DataFrame(grid_data), date_list

# --- STREAMLIT APP LOGIC ---
def main():
    load_css(); ensure_csv_structure()
    st.sidebar.title("📚 AMS Portal")
    if "logged_in" not in st.session_state:
        menu = st.sidebar.selectbox("Select Option", ["Login", "Register Student"])
    else:
        menu = st.sidebar.selectbox("Select Option", ["Dashboard", "Logout"])

    # --- LOGIN ---
    if menu == "Login":
        st.markdown('<div class="main-header"><h1>🎓 Secure Login</h1></div>', unsafe_allow_html=True)
        with st.container():
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                with st.form("login_form"):
                    st.markdown('<div class="card"><h3>🔐 Welcome Back</h3>', unsafe_allow_html=True)
                    uname = st.text_input("Username")
                    pwd = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        users = load_users()
                        user = users[(users["username"] == uname) & (users["password_hash"] == hash_password(pwd))]
                        if not user.empty:
                            st.session_state.update({"logged_in":True, "username":uname, "role":user.iloc[0]['role'], "user_name":user.iloc[0]['name'], "class_name":user.iloc[0]['class_name']})
                            st.rerun()
                        else: st.error("Invalid Credentials!")

    # --- STUDENT SELF REGISTRATION ---
    elif menu == "Register Student":
        st.markdown('<div class="main-header"><h1>📝 Student Registration</h1></div>', unsafe_allow_html=True)
        with st.container():
            c1,c2,c3 = st.columns([1,2,1])
            with c2:
                with st.form("reg_student"):
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    name = st.text_input("Full Name")
                    uname = st.text_input("Desired Username")
                    cls = st.text_input("Class/Batch (e.g. CS-2026)")
                    pwd = st.text_input("Password", type="password")
                    if st.form_submit_button("Register"):
                        users = load_users()
                        if uname in users["username"].values: st.error("Username taken!")
                        elif not uname or not pwd: st.error("Fill all fields!")
                        else:
                            new_row = pd.DataFrame([[uname, hash_password(pwd), "Student", name, "", "", "Student", cls, "self"]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
                            users = pd.concat([users, new_row], ignore_index=True)
                            save_users(users); generate_qr(uname)
                            st.success(f"Registered {name}! You can now login.")
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- DASHBOARDS ---
    elif menu == "Dashboard" and "logged_in" in st.session_state:
        role = st.session_state["role"]; curr_user = st.session_state["username"]; curr_class = st.session_state["class_name"]
        if st.sidebar.button("🚪 Logout"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

        # HEAD TEACHER (NAJEEB)
        if role == "HeadTeacher":
            st.markdown('<div class="main-header"><h1>👑 Head Teacher Dashboard</h1></div>', unsafe_allow_html=True)
            t1, t2 = st.tabs(["➕ Add Teacher", "📊 All Attendance"])
            with t1:
                with st.form("add_teacher"):
                    name = st.text_input("Teacher Name"); uname = st.text_input("Teacher Username"); pwd = st.text_input("Password", type="password")
                    cls = st.text_input("Assigned Class/Batch"); prof = st.text_input("Profession")
                    if st.form_submit_button("Add Teacher"):
                        users = load_users()
                        if uname in users["username"].values: st.error("Username exists!")
                        else:
                            new_row = pd.DataFrame([[uname, hash_password(pwd), "Teacher", name, "", "", prof, cls, "najeeb"]], columns=["username", "password_hash", "role", "name", "email", "phone", "profession", "class_name", "created_by"])
                            users = pd.concat([users, new_row], ignore_index=True); save_users(users); generate_qr(uname)
                            st.success(f"Teacher {name} added! Check 'My QR' tab in Teacher Dashboard.")
            with t2:
                grid_df, dates = get_attendance_grid(load_users()["username"].tolist(), days=30)
                st.dataframe(grid_df.style.map(lambda x: 'background-color: #f8d7da' if 'A'==str(x) else ('background-color: #d4edda' if 'P' in str(x) else ('background-color: #fff3cd' if 'L'==str(x) else ''))), use_container_width=True)

        # TEACHER
        elif role == "Teacher":
            st.markdown('<div class="main-header"><h1>🧑‍🏫 Teacher Dashboard</h1></div>', unsafe_allow_html=True)
            students = load_users()[(load_users()["class_name"]==curr_class) & (load_users()["role"]=="Student")]["username"].tolist()
            view = [curr_user] + students
            t1, t2, t3, t4 = st.tabs(["Mark Attendance", "Grid View", "Details", "My QR"])
            with t1:
                action = st.radio("Action", ["Check In", "Check Out", "Mark Leave"], horizontal=True)
                pwd = st.text_input("Enter Your Password", type="password")
                qr = st.file_uploader("Upload Your QR", type=['png','jpg'])
                if qr and st.button("Submit Attendance"):
                    if not pwd: st.error("Password required!")
                    else:
                        s, m = mark_attendance_qr(qr, curr_user, pwd, action)
                        st.success(m) if s else st.error(m)
            with t2:
                grid, dates = get_attendance_grid(view, days=30)
                st.dataframe(grid.style.map(lambda x: 'background-color: #f8d7da' if 'A'==str(x) else ('background-color: #d4edda' if 'P' in str(x) else ('background-color: #fff3cd' if 'L'==str(x) else ''))), use_container_width=True)
            with t3: st.dataframe(load_attendance()[load_attendance()["username"].isin(view)])
            with t4:
                qr_path = f"qr_codes/{curr_user}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, width=200)
                    with open(qr_path, "rb") as f: # FIXED DOWNLOAD BUTTON ERROR
                        st.download_button("⬇️ Download QR", f.read(), file_name=f"{curr_user}_qr.png")
                else: st.warning("QR not found!")

        # STUDENT
        elif role == "Student":
            st.markdown('<div class="main-header"><h1>🧑‍🎓 Student Dashboard</h1></div>', unsafe_allow_html=True)
            t1, t2, t3 = st.tabs(["Mark Attendance", "My Stats", "My QR"])
            with t1:
                action = st.radio("Action", ["Check In", "Check Out", "Mark Leave"], horizontal=True)
                pwd = st.text_input("Enter Your Password", type="password")
                qr = st.file_uploader("Upload Your QR", type=['png','jpg'])
                if qr and st.button("Submit Attendance"):
                    if not pwd: st.error("Password required!")
                    else:
                        s, m = mark_attendance_qr(qr, curr_user, pwd, action)
                        st.success(m) if s else st.error(m)
            with t2:
                grid, dates = get_attendance_grid([curr_user], days=30)
                st.dataframe(grid.style.map(lambda x: 'background-color: #f8d7da' if 'A'==str(x) else ('background-color: #d4edda' if 'P' in str(x) else ('background-color: #fff3cd' if 'L'==str(x) else ''))), use_container_width=True)
                st.dataframe(load_attendance()[load_attendance()["username"]==curr_user])
            with t3:
                qr_path = f"qr_codes/{curr_user}.png"
                if os.path.exists(qr_path):
                    st.image(qr_path, width=200)
                    with open(qr_path, "rb") as f: # FIXED DOWNLOAD BUTTON ERROR
                        st.download_button("⬇️ Download QR", f.read(), file_name=f"{curr_user}_qr.png")
                else: st.warning("QR not found!")

    elif menu == "Logout":
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if __name__ == "__main__": main()
