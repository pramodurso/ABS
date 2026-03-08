from .utils import *
from fastapi import status
from backend.database import get_db
from backend.routers.auth import get_current_user
from datetime import datetime

@pytest.fixture(autouse=True )
def set_patient_profile():
  app.dependency_overrides[get_db]=override_get_db
  app.dependency_overrides[get_current_user]=override_get_current_patient
  yield
  app.dependency_overrides.clear()


########## get_all_appointements_endpoint ##########
def test_get_all_appointments(test_db,profiles_db,users_db):
  response=client.get("/appointments/")
  assert response.status_code==status.HTTP_200_OK
  assert response.json()==[{"appointment_id":1,
                            "user_id":2,
                            "hospital_id":1,
                            "hospital_name": "Ramakrishna",
                            "description":"Shoulder dislocation",
                            "patient_id":1,
                            "doctor_id":1,
                            "appointment_date":"2026-03-30",
                            "start_time":"10:00:00",
                            "end_time":"10:30:00",
                            "status":'pending'}]

def test_get_all_appointments_profile_not_exists(test_db,users_db):
  response=client.get("/appointments/")
  assert response.status_code==status.HTTP_403_FORBIDDEN
  assert response.json()=={"detail":"Profile required to access this resource"}


###### Tests for get_available_slots endpoint ######
def test_get_available_slots(test_db,schedules_db,profiles_db,users_db):
  response=client.get("/appointments/available_slots/1/2026-03-30")

  assert response.status_code==status.HTTP_200_OK
  assert response.json()==["09:00:00",
                           "09:30:00",
                           "10:30:00",
                           "11:00:00",
                           "11:30:00",
                           "12:00:00",
                           "12:30:00",
                           "13:00:00",
                           "13:30:00",]

def test_get_available_slots_profile_not_exists(test_db,schedules_db,users_db):
  response=client.get("/appointments/available_slots/1/2026-03-30")

  assert response.status_code==status.HTTP_403_FORBIDDEN
  assert response.json()=={"detail":"Profile required to access this resource"}
  
def test_get_available_slots_doctor_not_found(test_db,schedules_db,profiles_db):
  response=client.get("/appointments/available_slots/999/2026-03-30")

  assert response.status_code==status.HTTP_404_NOT_FOUND
  assert response.json()=={"detail":"Doctor with doctor_id 999 doesn't exist."}

def test_get_available_slots_schedule_not_found_on_requested_day(test_db,schedules_db,profiles_db):
  response=client.get("/appointments/available_slots/1/2026-03-31")

  assert response.status_code==status.HTTP_404_NOT_FOUND
  assert response.json()=={"detail":"Doctor doesn't have schedule on WeekDay.TUESDAY"}


####### get_all_appointments_endpoint ######
def test_new_appointment(profiles_db,schedules_db,users_db):
  request_data={
    "hospital_id":1,
    "hospital_name":"Ramakrishna",
    "description":"Fracture",
    "doctor_id":1,
    "appointment_date":"2026-03-23",
    "start_time":"13:00:00"
  }

  response=client.post("/appointments/new_appointment",json=request_data)
  
  assert response.status_code==status.HTTP_201_CREATED
  
  db=TestLocalSession()
  model=db.query(Appointments).filter(Appointments.appointment_id==1).first()

  assert model.appointment_date==date(2026, 3, 23)
  assert model.description=="Fracture"
  assert model.doctor_id==1
  assert model.hospital_id==1
  assert model.hospital_name=="Ramakrishna"
  assert model.patient_id==1
  assert model.start_time==time(13, 0)
  assert model.end_time==time(13, 30)
  assert model.status==AppointmentStatus.PENDING
  assert model.user_id==2


def test_new_appointment_profile_not_exists(schedules_db,users_db):
  request_data={
    "hospital_id":1,
    "hospital_name":"Ramakrishna",
    "description":"Fracture",
    "doctor_id":1,
    "appointment_date":"2026-03-23",
    "start_time":"13:00:00"
  }
    
  response=client.post("/appointments/new_appointment",json=request_data)

  assert response.status_code==status.HTTP_403_FORBIDDEN
  assert response.json()=={"detail":"Profile required to access this resource"}


def test_new_appointment_conflict_appointment_with_same_doctor(test_db,profiles_db,schedules_db,users_db):
  request_data={
    "hospital_id":1,
    "hospital_name":"Ramakrishna",
    "description":"Fracture",
    "doctor_id":1,
    "appointment_date":"2026-03-23",
    "start_time":"13:00:00"
  }

  response=client.post("/appointments/new_appointment",json=request_data)

  assert response.status_code==status.HTTP_409_CONFLICT
  assert response.json()=={"detail":"Patient with user id- 2 already has an appointment with doctor 1"}

def test_new_appointment_doctor_has_not_created_schedule(profiles_db,users_db):
  request_data={
  "hospital_id":1,
  "hospital_name":"Ramakrishna",
  "description":"Fracture",
  "doctor_id":1,
  "appointment_date":"2026-03-23",
  "start_time":"13:00:00"
  }

  response=client.post("/appointments/new_appointment",json=request_data)

  assert response.status_code==status.HTTP_400_BAD_REQUEST
  assert response.json()=={"detail":"Doctor has not created a schedule yet. Please choose a different doctor."}




#### update_existing_appointment_endpoint ######

def test_update_existing_appointment(users_db,schedules_db,test_db,profiles_db):
  request_data={"appointment_date":"2026-03-23",
                "start_time":"10:30:00",
                "description":"Rickets"}
  response=client.put("/appointments/update_appointment/1",json=request_data)

  assert response.status_code==status.HTTP_204_NO_CONTENT
  db=TestLocalSession()

  model=db.query(Appointments).filter(Appointments.appointment_id==1).first()
  assert model.appointment_date==date(2026, 3, 23)
  assert model.start_time==time(10,30)
  assert model.description=="Rickets"
  


def test_update_existing_appointment_not_found_appointemnt(users_db,schedules_db,profiles_db):
  request_data={"appointment_date":"2026-03-23",
                "start_time":"10:30:00",
                "description":"Rickets"}
  response=client.put("/appointments/update_appointment/1",json=request_data)

  assert response.status_code==status.HTTP_404_NOT_FOUND

  assert response.json()=={"detail":"Appointment not found"}


def test_update_existing_appointment_conflict_past_dates(users_db,schedules_db,profiles_db,test_db):
  
  request_data={"appointment_date":"2026-03-07",
                "start_time":"10:30:00",
                "description":"Rickets"}
  response=client.put("/appointments/update_appointment/1",json=request_data)

  assert response.status_code==status.HTTP_409_CONFLICT

  assert response.json()=={"detail":"Cannot update appointments to past dates."}


def test_update_existing_appointment_conflict_atleast_2hr_window(users_db,schedules_db,profiles_db,test_db):
  request_date=str(datetime.now().date())
  request_data={"appointment_date":request_date,
                "start_time":"10:30:00",
                "description":"Rickets"}
  response=client.put("/appointments/update_appointment/1",json=request_data)

  assert response.status_code==status.HTTP_409_CONFLICT

  assert response.json()=={"detail":"Appointments must be scheduled at least around 2 hours in advance. Please choose a different time slot."}


def test_update_existing_appointment_badreq_doctor_doesnnot_work_on_requested_date(users_db,schedules_db,profiles_db,test_db):
  request_data={"appointment_date":"2026-03-29",
                "start_time":"10:30:00",
                "description":"Rickets"}
  response=client.put("/appointments/update_appointment/1",json=request_data)

  assert response.status_code==status.HTTP_400_BAD_REQUEST
  assert response.json()=={"detail":"Doctor doesn't work on Sunday"}




###### update_appointment_status_endpoint ############
def test_update_appointment_status(users_db,schedules_db,profiles_db,test_db):
  app.dependency_overrides[get_current_user]=override_get_current_doctor
  response=client.put("/appointments/update_appointment_status/1/confirmed")
  try:
    assert response.status_code==status.HTTP_204_NO_CONTENT
    db=TestLocalSession()
    model=db.query(Appointments).filter(Appointments.appointment_id==1).first()
    
    assert model.status==AppointmentStatus.CONFIRMED
  finally:
    app.dependency_overrides[get_current_user]=override_get_current_patient


####### cancel_appointment_endpoint ##########
def test_cancel_appointment(users_db,schedules_db,profiles_db,test_db):
  response=client.delete("/appointments/cancel_appointment/1")
  assert response.status_code==status.HTTP_204_NO_CONTENT
  
  db=TestLocalSession()
  model=db.query(Appointments).filter(Appointments.appointment_id==1).first()
  assert model is None

