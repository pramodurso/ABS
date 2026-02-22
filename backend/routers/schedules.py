from fastapi import Depends,HTTPException,status,APIRouter,Path
from pydantic import BaseModel,Field
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DoctorProfile,PatientProfile,Schedule,WeekDay
from .auth import get_current_user
from datetime import time,datetime,timedelta

router=APIRouter(
  prefix="/schedules",
  tags=["schedules"]
)

db_dependancy=Annotated[Session,Depends(get_db)]
user_dependancy=Annotated[dict,Depends(get_current_user)]

class ScheduleCreateRequest(BaseModel):
  slot_duration:time=Field(...,description="Duration of each appointment slot in HH:MM:SS format")
  day_of_week: WeekDay=Field(...,description="Day of the week for the schedule. Allowed values: monday, tuesday, wednesday, thursday, friday, saturday, sunday")
  start_time: time=Field(...,description="Start time of the schedule in HH:MM:SS format")
  end_time: time=Field( ...,description="End time of the schedule in HH:MM:SS format")

class ScheduleUpdateRequest(BaseModel):
  slot_duration:Optional[time]=Field(default=None,description="Duration of each appointment slot in HH:MM:SS format")
  day_of_week: Optional[WeekDay]=Field(default=None,description="Day of the week for the schedule. Allowed values: monday, tuesday, wednesday, thursday, friday, saturday, sunday")
  start_time: Optional[time]=Field(default=None,description="Start time of the schedule in HH:MM:SS format")
  end_time: Optional[time]=Field(default=None,description="End time of the schedule in HH:MM:SS format")

@router.get("/",status_code=status.HTTP_200_OK)
def get_doctor_schedule(db:db_dependancy,user:user_dependancy):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")

  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  
  doctor_profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not doctor_profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  return db.query(Schedule).filter(Schedule.doctor_id==doctor_profile_exists.id).all()



@router.post("/new_schedule",status_code=status.HTTP_201_CREATED)
def create_new_schedule(db:db_dependancy,user:user_dependancy,new_schedule_request:ScheduleCreateRequest):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")

  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")

  doctor_profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not doctor_profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  
  if new_schedule_request.start_time>=new_schedule_request.end_time:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="start_time must be before end_time")

  schedule_exists=db.query(Schedule).filter(Schedule.doctor_id==doctor_profile_exists.id).filter(Schedule.day_of_week==new_schedule_request.day_of_week).all()

  for schedule in schedule_exists:
    if new_schedule_request.start_time<schedule.end_time and new_schedule_request.end_time>schedule.start_time:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="A schedule already exists for this doctor at your requestion time slot. Please update the existing schedule or create a new one with a valid time slot.")

  new_schedule=Schedule(**new_schedule_request.model_dump(),doctor_id=doctor_profile_exists.id)
  db.add(new_schedule)
  db.commit()



@router.put("/update_schedule/{schedule_id}",status_code=status.HTTP_204_NO_CONTENT)
def update_schedule(db:db_dependancy,user:user_dependancy,updated_schedule_request:ScheduleUpdateRequest,schedule_id:int=Path(...,gt=0)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")

  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")

  doctor_profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not doctor_profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")

  model=db.query(Schedule).filter(Schedule.schedule_id==schedule_id).first()
  if model is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Schedule not found for this doctor")
  
  update_times=False
  if updated_schedule_request.start_time is not None and updated_schedule_request.end_time is not None:
    if updated_schedule_request.start_time >= updated_schedule_request.end_time:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="start_time must be before end_time")
    update_times=True

  schedule_exists=db.query(Schedule).filter(Schedule.doctor_id==doctor_profile_exists.id).filter(Schedule.day_of_week==updated_schedule_request.day_of_week).filter(Schedule.schedule_id!=schedule_id).all()
  for schedule in schedule_exists:
    if updated_schedule_request.start_time<schedule.end_time and updated_schedule_request.end_time>schedule.start_time:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="A schedule already exists for this doctor at your requestion time slot. Please update the existing schedule or create a new one with a valid time slot.")


  if update_times==True:
    model.start_time = updated_schedule_request.start_time
    model.end_time = updated_schedule_request.end_time

  if updated_schedule_request.slot_duration is not None:
    model.slot_duration = updated_schedule_request.slot_duration

  if updated_schedule_request.day_of_week is not None:
    model.day_of_week = updated_schedule_request.day_of_week

  db.commit()



@router.delete("/delete_schedule/{schedule_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(db:db_dependancy,user:user_dependancy,schedule_id:int=Path(...,gt=0)):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")

  doctor_profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not doctor_profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")

  model=db.query(Schedule).filter(Schedule.schedule_id==schedule_id).first()
  if model is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Schedule not found for this doctor")
  db.delete(model)
  db.commit()