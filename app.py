import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIG & CSS ---
st.set_page_config(page_title="AMS Cloud CSV", layout="centered", page_icon="🎓")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e3799; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        background-color: #1e3799; color: white; border-radius: 6px; width: 100%;
        font-weight: bold; padding: 10px; border: none;
    }
    .stButton>button:hover { background-color: #4a69bd; }
    </style>
""", unsafe_allow_html=True)

# --- CSV DATA CORE LOGIC ---
USERS_FILE = "users.csv"
ATTENDANCE_FILE = "attendance_cloud.csv"

def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Load current data into session state
if 'users_df' not in st.session_state:
    st.session_state.users_df = load_data(USERS_FILE, ["username", "password", "role"])
if 'attendance_df' not in st.session_state:
    st.session_state.attendance_df = load_data(ATTENDANCE_FILE, ["username", "date", "status", "method"])

# --- DASHBOARDS ---
def student_dashboard(username):
    st.title(f"🎓 Student Portal: {username}")
    
    method = st.selectbox("Select Attendance Method:", ["Face Recognition (Camera)", "QR Code Simulation"])
    date_today = datetime.now().strftime("%Y-%m-%d")
    
    if method == "Face Recognition (Camera)":
        img = st.camera_input("Verify your face")
        if img and st.button("Mark Attendance"):
            df = st.session_state.attendance_df
            # Check duplicate
            if not ((df['username'] == username) & (df['date'] == date_today)).any():
                new_row = pd.DataFrame([[username, date_today, "Present", "Face"]], columns=df.columns)
                st.session_state.attendance_df = pd.concat([df, new_row], ignore_index=True)
                save_data(st.session_state.attendance_df, ATTENDANCE_FILE)
                st.success("✅ Attendance Marked via Face Recognition!")
            else:
                st.warning("⚠️ Already marked for today.")
    else:
        if st.button("Scan QR & Mark Attendance"):
            df = st.session_state.attendance_df
            if not ((df['username'] == username) & (df['date'] == date_today)).any():
                new_row = pd.DataFrame([[username, date_today, "Present", "QR"]], columns=df.columns)
                st.session_state.attendance_df = pd.concat([df, new_row], ignore_index=True)
                save_data(st.session_state.attendance_df, ATTENDANCE_FILE)
                st.success("✅ Attendance Marked via QR Code!")
            else:
                st.warning("⚠️ Already marked for today.")

    st.divider()
    st.subheader("📊 Your Attendance Records")
    df = st.session_state.attendance_df
    student_df = df[df['username'] == username]
    if not student_df.empty:
        st.dataframe(student_df, use_container_width=True)
        st.bar_chart(student_df['date'].value_counts())
    else:
        st.info("No history found.")

def teacher_dashboard():
    st.title("👨‍🏫 Teacher Cloud Dashboard")
    
    menu = st.sidebar.radio("Menu", ["View Attendance", "Register Student", "Cloud Backup & Sync"])
    
    if menu == "Register Student":
        st.subheader("➕ Add New Student")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            df = st.session_state.users_df
            if new_user not in df['username'].values:
                new_row = pd.DataFrame([[new_user, new_pass, "Student"]], columns=df.columns)
                st.session_state.users_df = pd.concat([df, new_row], ignore_index=True)
                save_data(st.session_state.users_df, USERS_FILE)
                st.success("✅ Student Registered!")
            else:
                st.error("❌ Username already exists.")
                
    elif menu == "View Attendance":
        st.subheader("📊 Complete Class Attendance")
        df = st.session_state.attendance_df
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.line_chart(df.groupby('date').size())
        else:
            st.info("No records yet.")
            
    elif menu == "Cloud Backup & Sync":
        st.subheader("💾 Backup Your CSV Data")
        st.write("Streamlit Cloud resets files periodically. Download or upload your data to keep it safe.")
        
        # Download buttons
        att_csv = st.session_state.attendance_df.to_csv(index=False)
        st.download_button("📥 Download Attendance CSV", data=att_csv, file_name="attendance_cloud.csv", mime="text/csv")
        
        # Upload tool
        uploaded_file = st.file_uploader("📤 Upload Existing Attendance CSV to Sync", type="csv")
        if uploaded_file is not None:
            st.session_state.attendance_df = pd.read_csv(uploaded_file)
            save_data(st.session_state.attendance_df, ATTENDANCE_FILE)
            st.success("✅ Attendance synced successfully!")

# --- MAIN APP ---
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.update({'logged_in': False, 'username': "", 'role': ""})

    if not st.session_state['logged_in']:
        st.markdown("<h2 style='text-align: center;'>AMS Cloud Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            df = st.session_state.users_df
            user_match = df[(df['username'] == username) & (df['password'].astype(str) == password)]
            if not user_match.empty:
                st.session_state.update({'logged_in': True, 'username': username, 'role': user_match.iloc[0]['role']})
                st.rerun()
            else:
                st.error("Invalid Credentials!")
    else:
        st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
        if st.session_state['role'] == "Student":
            student_dashboard(st.session_state['username'])
        else:
            teacher_dashboard()

if __name__ == '__main__':
    main()
