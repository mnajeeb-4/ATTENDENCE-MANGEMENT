import streamlit as st
import bcrypt
from sqlalchemy.orm import sessionmaker
from models import User, SessionLocal, engine

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'role' not in st.session_state:
        st.session_state.role = None

def login_user(username, password):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if user and verify_password(password, user.password_hash):
        st.session_state.logged_in = True
        st.session_state.user_id = user.id
        st.session_state.role = user.role
        st.session_state.full_name = user.full_name
        return True
    return False

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.role = None
    st.rerun()

def create_user(username, password, role, full_name, class_id=None):
    db = SessionLocal()
    hashed = hash_password(password)
    new_user = User(username=username, password_hash=hashed, role=role, full_name=full_name, class_id=class_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return new_user.id
