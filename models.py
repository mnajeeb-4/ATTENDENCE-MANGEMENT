from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date

Base = declarative_base()
engine = create_engine('sqlite:///ams.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'STUDENT' or 'TEACHER'
    full_name = Column(String, nullable=False)
    class_id = Column(String, nullable=True)  # Only for students

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    face_encoding = Column(String, nullable=True)  # Stored as base64 string
    user = relationship("User")

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date, default=date.today)
    status = Column(String, default='A')  # P=Present, A=Absent, HL=Half Leave, WK=Weekend
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    total_working_hours = Column(Float, default=0.0)
    late_in_hours = Column(Float, default=0.0)
    early_out_hours = Column(Float, default=0.0)

Base.metadata.create_all(engine)
