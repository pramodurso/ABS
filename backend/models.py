from sqlalchemy import Column, ForeignKey, Integer, String, Time, Enum, Date
from .database import Base
import enum

class Users(Base):
  __tablename__="users"

  user_id=Column(Integer,primary_key=True,index=True)
  username=Column(String,unique=True)
  email=Column(String,unique=True)
  hashed_password=Column(String)
  role=Column(String)

class PatientProfile(Base):
  __tablename__="patients"
  
  id=Column(Integer,primary_key=True,index=True)
  user_id=Column(Integer,ForeignKey("users.user_id"),unique=True)
  firstname=Column(String)
  lastname=Column(String)
  age=Column(Integer)
  phone_number=Column(String)

class DoctorProfile(Base):
  __tablename__="doctors"
  
  id=Column(Integer,primary_key=True,index=True)
  user_id=Column(Integer,ForeignKey("users.user_id"),unique=True)
  firstname=Column(String)
  lastname=Column(String)
  age=Column(Integer)
  phone_number=Column(String)
  department=Column(String)     



class WeekDay(enum.Enum):
  MONDAY="monday"
  TUESDAY="tuesday"
  WEDNESDAY="wednesday"
  THURSDAY="thursday"
  FRIDAY="friday"
  SATURDAY="saturday"
  SUNDAY="sunday"

class AppointmentStatus(enum.Enum):
  PENDING="pending"
  CONFIRMED="confirmed"
  CANCELLED="cancelled"
  COMPLETED="completed"


class Appointments(Base):
  __tablename__="appointments"

  appointment_id=Column(Integer, primary_key=True, index=True)
  user_id=Column(Integer,ForeignKey("users.user_id"))
  hospital_id=Column(Integer)
  hospital_name=Column(String)
  description=Column(String)
  patient_id=Column(Integer,ForeignKey("patients.id"))
  doctor_id=Column(Integer,ForeignKey("doctors.id"))
  appointment_date=Column(Date, nullable= False)
  start_time=Column(Time, nullable=False)
  end_time=Column(Time,nullable=False)
  status=Column(Enum(AppointmentStatus),nullable=False)



class Schedule(Base):
  __tablename__="schedule"

  schedule_id=Column(Integer,primary_key=True,index=True)
  doctor_id=Column(Integer,ForeignKey("doctors.id"))
  slot_duration=Column(Time, nullable=False)
  day_of_week=Column(Enum(WeekDay),nullable= False)
  start_time=Column(Time, nullable=False)
  end_time=Column(Time,nullable=False)

  
