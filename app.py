import streamlit as st
import pandas as pd
import datetime
import qrcode
import os
import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import io

# --- PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="Modern AMS", layout="wide", page_icon="🎓")

# Custom HTML/CSS for Professional UI
st.markdown("""
<style>
    .main {background-color: #f4f6f9;}
    h1 {color: #1E3A8A; font-family: 'Arial', sans-serif; font-weight: bold;}
    h2, h3 {color: #3B82F6;}
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px; 
        padding: 10px 24px; font-weight: bold; border: none; transition: 0.3s;
    }
    .stButton>button:hover {background-color: #1D4ED8; color: white;}
    .dataframe {border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    div[data-testid="stMetricValue"] {font-size: 24px; color: #10B981;}
</style>
""", unsafe_allow_html=True)

# --- DATABASE (CSV) INITIALIZATION ---
USER_FILE = "users.csv"
ATTENDANCE_FILE = "attendance.csv"

def init_db():
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["User_ID", "Name", "Role", "Email", "Phone", "Password", "Class_Batch", "Profession"])
        # Inject default teacher 'najeeb'
        df.loc[0] = ["T-100", "najeeb", "Teacher", "najeeb@school.com", "0000000000", "inajeeb123", "All", "Head Teacher"]
        df.to_csv(USER_FILE, index=False)
    
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=["User_ID", "Name", "Role", "Date", "Time_IN", "Time_OUT"])
        df.to_csv(ATTENDANCE_FILE, index=False)

init_db()

# --- HELPER FUNCTIONS ---
def get_users(): return pd.read_csv(USER_FILE)
def get_attendance(): return pd.read_csv(ATTENDANCE_FILE)
def save_user(df): df.to_csv(USER_FILE, index=False)
def save_attendance(df): df.to_csv(ATTENDANCE_FILE, index=False)

def generate_qr(user_id, name):
    data = f"{user_id}"
    qr = qrcode.make(data)
    img_byte_arr = io.BytesIO()
    qr.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def mark_attendance(user_id):
    users = get_users()
    user = users[users['User_ID'] == user_id]
    
    if user.empty:
        return False, "Invalid QR Code! User not found."
    
    name = user.iloc[0]['Name']
    role = user.iloc[0]['Role']
    
    att_df = get_attendance()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Check if already marked IN today
    today_records = att_df[(att_df['User_ID'] == user_id) & (att_df['Date'] == today)]
    
    if today_records.empty:
        # Mark IN
        new_record = pd.DataFrame([{"User_ID": user_id, "Name": name, "Role": role, "Date": today, "Time_IN": current_time, "Time_OUT": "-"}])
        att_df = pd.concat([att_df, new_record], ignore_index=True)
        save_attendance(att_df)
        return True, f"Welcome {name}! IN time marked at {current_time}."
    else:
        # Mark OUT
        idx = today_records.index[0]
        if att_df.at[idx, 'Time_OUT'] == "-":
            att_df.at[idx, 'Time_OUT'] = current_time
            save_attendance(att_df)
            return True, f"Goodbye {name}! OUT time (Leave) marked at {current_time}."
        else:
            return False, f"{name}, your IN and OUT attendance is already complete for today."

# --- AUTHENTICATION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None

# --- APP ROUTING ---
if not st.session_state.logged_in:
    st.title("🎓 Attendance Management System")
    
    tab1, tab2 = st.tabs(["Login", "Teacher Registration"])
    
    with tab1:
        st.subheader("Login to your account")
        col1, col2 = st.columns([1, 2])
        with col1:
            log_id = st.text_input("User ID (e.g., T-100 or S-101)")
            log_pass = st.text_input("Password", type="password")
            if st.button("Login"):
                users = get_users()
                user = users[(users['User_ID'] == log_id) & (users['Password'] == log_pass)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user.iloc[0]
                    st.rerun()
                else:
                    st.error("Invalid ID or Password!")
                    
    with tab2:
        st.subheader("Register as a New Teacher")
        t_name = st.text_input("Full Name")
        t_email = st.text_input("Email")
        t_phone = st.text_input("Phone Number")
        t_prof = st.text_input("Profession (e.g., Math Teacher)")
        t_pass = st.text_input("Create Password", type="password")
        
        if st.button("Register Teacher"):
            if t_name and t_pass:
                users = get_users()
                new_id = f"T-{len(users) + 100}"
                new_teacher = pd.DataFrame([{"User_ID": new_id, "Name": t_name, "Role": "Teacher", "Email": t_email, "Phone": t_phone, "Password": t_pass, "Class_Batch": "All", "Profession": t_prof}])
                save_user(pd.concat([users, new_teacher], ignore_index=True))
                st.success(f"Registered Successfully! Your User ID is **{new_id}**. Please Login.")
            else:
                st.warning("Name and Password are required.")

else:
    # --- DASHBOARDS ---
    user_info = st.session_state.user_data
    
    st.sidebar.title(f"Welcome, {user_info['Name']}")
    st.sidebar.markdown(f"**Role:** {user_info['Role']}")
    if user_info['Role'] == 'Teacher':
        st.sidebar.markdown(f"**Profession:** {user_info['Profession']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.rerun()

    # --- TEACHER DASHBOARD ---
    if user_info['Role'] == "Teacher":
        st.title("👨‍🏫 Teacher Dashboard")
        menu = st.radio("Navigation", ["Overview & My Attendance", "Manage Students", "Scan QR (Mark Attendance)"], horizontal=True)
        
        if menu == "Overview & My Attendance":
            st.subheader("Your Attendance Records")
            att_df = get_attendance()
            my_att = att_df[att_df['User_ID'] == user_info['User_ID']]
            st.dataframe(my_att, use_container_width=True)
            
            st.subheader("Class Attendance Overview")
            st.dataframe(att_df, use_container_width=True) # View all (or filter by batch logic here)
            
            # Simple visualization [cite: 29]
            if not att_df.empty:
                st.bar_chart(att_df['Date'].value_counts())
                
        elif menu == "Manage Students":
            st.subheader("Register a New Student")
            with st.form("student_form"):
                s_name = st.text_input("Student Name")
                s_batch = st.text_input("Class / Batch")
                s_pass = st.text_input("Default Password", value="student123")
                submitted = st.form_submit_button("Add Student & Generate QR")
                
                if submitted and s_name:
                    users = get_users()
                    new_s_id = f"S-{len(users) + 100}"
                    new_student = pd.DataFrame([{"User_ID": new_s_id, "Name": s_name, "Role": "Student", "Email": "-", "Phone": "-", "Password": s_pass, "Class_Batch": s_batch, "Profession": "-"}])
                    save_user(pd.concat([users, new_student], ignore_index=True))
                    
                    st.success(f"Student {s_name} added! ID: {new_s_id}")
                    qr_bytes = generate_qr(new_s_id, s_name)
                    st.image(qr_bytes, caption=f"QR Code for {s_name}")
                    st.download_button(label="Download QR", data=qr_bytes, file_name=f"{new_s_id}_QR.png", mime="image/png")

    # --- STUDENT DASHBOARD ---
    elif user_info['Role'] == "Student":
        st.title("🎓 Student Dashboard")
        menu = st.radio("Navigation", ["My Attendance", "Scan QR (Mark Attendance)"], horizontal=True)
        
        if menu == "My Attendance":
            st.subheader("My Attendance Records")
            att_df = get_attendance()
            my_att = att_df[att_df['User_ID'] == user_info['User_ID']]
            st.dataframe(my_att, use_container_width=True)
            
            # Personal Statistics 
            if not my_att.empty:
                st.line_chart(my_att['Date'].value_counts())

    # --- QR SCANNER LOGIC (Shared) ---
    if (user_info['Role'] == "Teacher" and menu == "Scan QR (Mark Attendance)") or \
       (user_info['Role'] == "Student" and menu == "Scan QR (Mark Attendance)"):
        st.subheader("📷 Scan QR Code to Mark IN / OUT")
        st.info("Pehli baar scan karne par IN time lagega, dusri baar scan karne par OUT (Leave) time lagega.")
        
        # Streamlit cloud-safe camera input
        img_file_buffer = st.camera_input("Take a picture of your QR Code")
        
        if img_file_buffer is not None:
            image = Image.open(img_file_buffer)
            decoded_objects = decode(image)
            
            if decoded_objects:
                for obj in decoded_objects:
                    scanned_id = obj.data.decode("utf-8")
                    
                    # Ensure students can't scan other's QR codes
                    if user_info['Role'] == 'Student' and scanned_id != user_info['User_ID']:
                        st.error("You can only scan your own QR code!")
                    else:
                        success, msg = mark_attendance(scanned_id)
                        if success:
                            st.success(msg)
                        else:
                            st.warning(msg)
            else:
                st.error("No QR code detected in the image. Please try again.")
