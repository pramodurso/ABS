from sqlalchemy import StaticPool, text
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from backend.models import Appointments,PatientProfile,DoctorProfile,AppointmentStatus,Users,Schedule,WeekDay
from datetime import date,time
from fastapi.testclient import TestClient
from backend.main import app
from backend.routers.auth import bcrypt_context
from backend.database import Base


TEST_DATABASE_URL="sqlite:///./test.db"

engine=create_engine(TEST_DATABASE_URL,
                     connect_args={"check_same_thread":False},
                     poolclass=StaticPool)

TestLocalSession=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
  db=TestLocalSession()
  try:
    yield db
  finally:
    db.close()

def override_get_current_patient():
  return {"username":"ashikaranganath","id":2,"role":"patient"}

def override_get_current_doctor():
  return {"username":"krishnakumar","id":1,"role":"doctor"}

client=TestClient(app)



@pytest.fixture
def empty_db():
  Base.metadata.drop_all(bind=engine)
  Base.metadata.create_all(bind=engine)
  db=TestLocalSession()

  try:
    yield db
  finally:
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(empty_db):
  db=empty_db

  model_appointments=Appointments(appointment_id=1,
                                  user_id=2,
                                  hospital_id=1,
                                  hospital_name="Ramakrishna",
                                  description="Shoulder dislocation",
                                  patient_id=1,
                                  doctor_id=1,
                                  appointment_date=date(2026,3,30),
                                  start_time=time(hour=10),
                                  end_time=time(hour=10,minute=30),
                                  status=AppointmentStatus.PENDING)
  

  db.add(model_appointments)
  db.commit()
  yield db


@pytest.fixture
def users_db(empty_db):
  db=empty_db

  model_user1=Users(user_id=1,
                  username="krsihnakumar",
                  email="krishna@gmail.com",
                  hashed_password=bcrypt_context.hash("iamdoctor"),
                  role="doctor"
                  )
  
  model_user2=Users(user_id=2,
                    username="ashikaranganath",
                    email="ashika@gmail.com",
                    hashed_password=bcrypt_context.hash("iampatient"),
                    role="patient"
                    )

  db.add(model_user1)
  db.add(model_user2)
  db.commit()
  yield db

  

@pytest.fixture
def schedules_db(empty_db):
  db=empty_db

  model_schedules=Schedule(schedule_id=1,
                           doctor_id=1,
                           slot_duration=time(minute=30),
                           day_of_week=WeekDay.MONDAY,
                           start_time=time(hour=9),
                           end_time=time(hour=14))
  
  db.add(model_schedules)
  db.commit()
  yield db
  



@pytest.fixture
def profiles_db(empty_db):
  db=empty_db
  model_doctors=DoctorProfile(id=1,
                              user_id=1,
                              firstname="Krishna",
                              lastname="Kumar",
                              age=30,
                              phone_number="123456789",
                              department="orthopaedic")
  
  model_patients=PatientProfile(id=1,
                                user_id=2,
                                firstname="Ashika",
                                lastname="Ranganath",
                                age=28,
                                phone_number="987654321")
  

  db.add(model_doctors)
  db.add(model_patients)
  db.commit()
  yield db


