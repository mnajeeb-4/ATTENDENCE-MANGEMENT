# models.py
from sqlalchemy import Column, Integer, String, Date, Time, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # Hashed password
    role = Column(String(20), nullable=False)       # 'teacher' or 'student'
    full_name = Column(String(100))
    class_name = Column(String(50))                 # Used for RBAC (Restrict teachers)

    attendances = relationship("Attendance", back_populates="user")

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, nullable=False)
    status = Column(String(10))                     # P, A, HL, WK
    in_time = Column(Time)
    out_time = Column(Time)
    total_hours = Column(Float, default=0.0)
    late_hours = Column(Float, default=0.0)
    early_hours = Column(Float, default=0.0)

    user = relationship("User", back_populates="attendances")
