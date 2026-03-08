from fastapi import APIRouter,status,Depends,Path,Query,HTTPException
from pydantic import BaseModel,Field
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Appointments,PatientProfile,DoctorProfile, Schedule, WeekDay, AppointmentStatus
from .auth import get_current_user
from datetime import date, time, datetime, timedelta
db_dependancy=Annotated[Session,Depends(get_db)]

user_dependancy=Annotated[dict,Depends(get_current_user)]

router=APIRouter(
  prefix="/appointments",
  tags=["appoinments"]
)

class CreateAppointmentRequest(BaseModel):
  hospital_id: int=Field(gt=0)
  hospital_name: str=Field(min_length=3)
  description:Optional[str]=Field(default=None)
  doctor_id:int=Field(gt=0)
  # Use proper types so Pydantic validates formats for us
  appointment_date: date = Field(...,description="Date of the appointment in YYYY-MM-DD format")
  start_time: time = Field(...,description="Start time of the appointment in HH:MM format")
  # Do not accept end_time from clients — we'll compute it server-side from the doctor's slot_duration


class UpdateAppointmentRequest(BaseModel):
  appointment_date:Optional[date]=Field(default=None,description="Date of the appointment in YYYY-MM-DD format")
  start_time:Optional[time]=Field(default=None,description="Start time of the appointment in HH:MM format")
  description:Optional[str]=Field(default=None)



@router.get("/",status_code=status.HTTP_200_OK)
def get_all_appointments(db:db_dependancy,user:user_dependancy):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  
  if (user.get('role')).lower()=="doctor":
    doctor_profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
    if not doctor_profile_exists:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
    
    doctor=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
    return db.query(Appointments).filter(Appointments.doctor_id==doctor.id).all()
  
  else:
    patient_profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
    if not patient_profile_exists:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
    
    return db.query(Appointments).filter(Appointments.user_id==user.get('id')).all()

@router.get("/available_slots/{doctor_id}/{date}",status_code=status.HTTP_200_OK)
def get_available_slots(db:db_dependancy,user:user_dependancy,doctor_id:int=Path(...,gt=0),date:date=Path(...)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")  
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  doctor_exists=db.query(DoctorProfile).filter(DoctorProfile.id==doctor_id).first()
  if not doctor_exists:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Doctor with doctor_id {doctor_id} doesn't exist.")
  requested_day=date.weekday()

  weekday={0:WeekDay.MONDAY, 1:WeekDay.TUESDAY, 2:WeekDay.WEDNESDAY, 3:WeekDay.THURSDAY, 4:WeekDay.FRIDAY, 5:WeekDay.SATURDAY, 6:WeekDay.SUNDAY}
  day=weekday.get(requested_day)
  schedules=db.query(Schedule).filter(Schedule.doctor_id==doctor_id).filter(Schedule.day_of_week==day).all()
  if not schedules:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Doctor doesn't have schedule on {day}")
  intervals=[]
  for schedule in schedules:
    interval=datetime.combine(date,schedule.start_time)
    schedule_end_time=datetime.combine(date,schedule.end_time)
    while(interval<schedule_end_time):
      intervals.append(interval.time())
      interval+=timedelta(hours=(schedule.slot_duration).hour,minutes=schedule.slot_duration.minute,seconds=schedule.slot_duration.second)
  
  booked_appointments=db.query(Appointments).filter(Appointments.doctor_id==doctor_id).filter(Appointments.appointment_date==date).filter(Appointments.status!=AppointmentStatus.CANCELLED).all()
  for b_appointment in booked_appointments:
    intervals.remove(b_appointment.start_time)
  return intervals


@router.post("/new_appointment",status_code=status.HTTP_201_CREATED)
def create_new_appointment(db:db_dependancy,user:user_dependancy,new_appointment_request:CreateAppointmentRequest):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")  
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  appointment_exist=db.query(Appointments).filter(Appointments.user_id==user.get('id')).filter(Appointments.doctor_id==new_appointment_request.doctor_id).first()
  if appointment_exist:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Patient with user id- {user.get('id')} already has an appointment with doctor {new_appointment_request.doctor_id}")
  
  doctor_created_schedule=db.query(Schedule).filter(Schedule.doctor_id==new_appointment_request.doctor_id).first()
  if not doctor_created_schedule:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Doctor has not created a schedule yet. Please choose a different doctor.")
  

  if new_appointment_request.appointment_date<datetime.now().date():
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Cannot create appointments for past dates.")
  requested_datetime=datetime.combine(new_appointment_request.appointment_date,new_appointment_request.start_time)
  diff_hours=round(((requested_datetime-datetime.now()).total_seconds())/3600)
  if diff_hours<2:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Appointments must be scheduled at least around 2 hours in advance. Please choose a different time slot.")
  
  weekday={0:WeekDay.MONDAY, 1:WeekDay.TUESDAY, 2:WeekDay.WEDNESDAY, 3:WeekDay.THURSDAY, 4:WeekDay.FRIDAY, 5:WeekDay.SATURDAY, 6:WeekDay.SUNDAY}
  day_entered=new_appointment_request.appointment_date.weekday()
  day=weekday.get(day_entered)


  doctor_schedule=db.query(Schedule).filter(Schedule.doctor_id==new_appointment_request.doctor_id,Schedule.day_of_week==day).first()
  if not doctor_schedule:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Doctor doesn't work on {day.value.capitalize()}")
  
  doctor_schedules=db.query(Schedule).filter(Schedule.doctor_id==new_appointment_request.doctor_id,Schedule.day_of_week==day).all()
  doctor_schedule=None

  for doctor_sched in doctor_schedules:
    if new_appointment_request.start_time>=doctor_sched.start_time and new_appointment_request.start_time<=doctor_sched.end_time:
      doctor_schedule=doctor_sched
      break
  if doctor_schedule is None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Doctor doesn't work on {day.value.capitalize()} at your requested time")
  
  time_slot=doctor_schedule.slot_duration
  duration_slot=timedelta(hours=time_slot.hour,minutes=time_slot.minute,seconds=time_slot.second)
  start_time=datetime.combine(new_appointment_request.appointment_date, new_appointment_request.start_time)
  new_start_time=start_time.time()
  new_end_time=(start_time+duration_slot).time()

  appointments_on_date=db.query(Appointments).filter(Appointments.user_id==user.get('id')).filter(Appointments.appointment_date==new_appointment_request.appointment_date).all()
  for appointmnent in appointments_on_date:
    if new_start_time<appointmnent.end_time and new_end_time>appointmnent.start_time:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Patient already has appointment on {new_appointment_request.appointment_date} at the requested time slot.")
    
  existing_schedules=db.query(Appointments).filter(Appointments.doctor_id==new_appointment_request.doctor_id, Appointments.appointment_date==new_appointment_request.appointment_date).filter(Appointments.status != AppointmentStatus.CANCELLED).all()
  for schedule in existing_schedules:
    if (new_start_time<schedule.end_time and new_end_time>schedule.start_time) or (new_end_time>schedule.start_time and new_end_time<=schedule.end_time):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="The doctor is not available at the selected time. Please choose a different time slot.")

  
  patient=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  new_appointment=Appointments(**new_appointment_request.model_dump(),user_id=user.get("id"),patient_id=patient.id,end_time=new_end_time,status=AppointmentStatus.PENDING)

  db.add(new_appointment)
  db.commit()




@router.put("/update_appointment/{appointment_id}",status_code=status.HTTP_204_NO_CONTENT)
def update_existing_appointment(db:db_dependancy,
                                user:user_dependancy,
                                updated_appointment_request:UpdateAppointmentRequest,
                                appointment_id:int=Path(gt=0)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  
  profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  
  model=db.query(Appointments).filter(Appointments.appointment_id==appointment_id).filter(Appointments.user_id==user.get('id')).first()
  if model is None:
    raise HTTPException(status_code=404,detail="Appointment not found")
  
  if updated_appointment_request.appointment_date or updated_appointment_request.start_time:
    if updated_appointment_request.appointment_date:
      actual_date=updated_appointment_request.appointment_date
      if actual_date<datetime.now().date():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Cannot update appointments to past dates.")
      day_entered=updated_appointment_request.appointment_date.weekday()
    else:
      actual_date=model.appointment_date
      day_entered=actual_date.weekday()

    if updated_appointment_request.start_time:
      actual_start_time=datetime.combine(actual_date, updated_appointment_request.start_time)
    else:
      actual_start_time=datetime.combine(actual_date, model.start_time)

    diff_hours=round(((actual_start_time-datetime.now()).total_seconds())/3600)
    if diff_hours<2:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Appointments must be scheduled at least around 2 hours in advance. Please choose a different time slot.")

    weekday={0:WeekDay.MONDAY, 1:WeekDay.TUESDAY, 2:WeekDay.WEDNESDAY, 3:WeekDay.THURSDAY, 4:WeekDay.FRIDAY, 5:WeekDay.SATURDAY, 6:WeekDay.SUNDAY}
    day=weekday.get(day_entered)
    doctor_schedules=db.query(Schedule).filter(Schedule.doctor_id==model.doctor_id,Schedule.day_of_week==day).all()
    doctor_schedule=None

    if not doctor_schedules:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Doctor doesn't work on {day.value.capitalize()}")

    for doctor_sched in doctor_schedules:
      # if doctor_sched.start_time>=updated_appointment_request.start_time and doctor_sched.start_time<=updated_appointment_request.end_time:
      if actual_start_time.time()>=doctor_sched.start_time and actual_start_time.time()<=doctor_sched.end_time:
        doctor_schedule=doctor_sched
        break
    if doctor_schedule is None:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Doctor doesn't work on {day.value.capitalize()} at your requested time")
    
    time_slot=doctor_schedule.slot_duration
    duration_slot=timedelta(hours=time_slot.hour,minutes=time_slot.minute,seconds=time_slot.second)
    new_start_time=actual_start_time.time()
    new_end_time=(actual_start_time+duration_slot).time()

    existing_schedules=db.query(Appointments).filter(Appointments.doctor_id==model.doctor_id, Appointments.appointment_date==updated_appointment_request.appointment_date).filter(Appointments.status!=AppointmentStatus.CANCELLED).all()
    for schedule in existing_schedules:
      if (new_start_time<schedule.end_time and new_end_time>schedule.start_time):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="The doctor is not available at the selected time. Please choose a different time slot.")
    
  if updated_appointment_request.description is not None:
    model.description = updated_appointment_request.description
  if updated_appointment_request.appointment_date is not None:
    model.appointment_date = updated_appointment_request.appointment_date
  if updated_appointment_request.start_time is not None or updated_appointment_request.appointment_date is not None:
    model.start_time = updated_appointment_request.start_time
    model.end_time = new_end_time  # Update end_time based on new start_time and doctor's slot_duration
  model.status = AppointmentStatus.PENDING  # Reset status to pending on any update for re-approval

  # Persist changes
  db.commit()


@router.put("/update_appointment_status/{appointment_id}/{appointment_status_updated}",status_code=status.HTTP_204_NO_CONTENT)
def update_appointment_status(db:db_dependancy,user:user_dependancy,appointment_id:int=Path(...,gt=0),appointment_status_updated:AppointmentStatus=Path(...)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failes")
  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="You are not allowed to access this endpoint because your role doesn't match.")
  
  profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")

  appointment=db.query(Appointments).filter(Appointments.appointment_id==appointment_id).first()
  if appointment is None:
    raise HTTPException(status_code=404,detail="Appointment not found")
  
  appointment.status=appointment_status_updated
  db.commit()
  


@router.delete("/cancel_appointment/{appointment_id}",status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(db:db_dependancy,user:user_dependancy,appointment_id:int=Path(...,gt=0)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")

  profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  
  model=db.query(Appointments).filter(Appointments.appointment_id==appointment_id).filter(Appointments.user_id==user.get('id')).first()

  if model is None:
    raise HTTPException(status_code=404,detail="Appointment not found")
  db.delete(model)
  db.commit()

  