from fastapi import Depends,HTTPException,status,APIRouter,Path,Query
from pydantic import BaseModel,Field
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DoctorProfile,PatientProfile,Schedule,WeekDay
from .auth import get_current_user
from datetime import time,datetime,timedelta
from .dependencies import get_current_active_doctor,get_current_active_patient

router=APIRouter(
  prefix="/schedules",
  tags=["schedules"]
)

db_dependancy=Annotated[Session,Depends(get_db)]
user_dependancy=Annotated[dict,Depends(get_current_user)]

patient_dependancy=Annotated[PatientProfile,Depends(get_current_active_patient)]
doctor_dependancy=Annotated[DoctorProfile,Depends(get_current_active_doctor)]

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
def get_doctor_schedule(db:db_dependancy,user:user_dependancy,doctor:doctor_dependancy,limit:int=Query(10,gt=1,le=100),skip:int=Query(0,ge=0)):
    total=db.query(Schedule).filter(Schedule.doctor_id==doctor.id).count()
    more_pages=skip+limit<total
    return {"schedules":db.query(Schedule).filter(Schedule.doctor_id==doctor.id).offset(skip).limit(limit).all(),
            "total":total,
            "offset":skip,
            "limit":limit,
            "more_pages":more_pages}




@router.post("/new_schedule",status_code=status.HTTP_201_CREATED)
def create_new_schedule(db:db_dependancy,user:user_dependancy,new_schedule_request:ScheduleCreateRequest,doctor:doctor_dependancy):
  
  if new_schedule_request.start_time>=new_schedule_request.end_time:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="start_time must be before end_time")

  schedule_exists=db.query(Schedule).filter(Schedule.doctor_id==doctor.id).filter(Schedule.day_of_week==new_schedule_request.day_of_week).all()

  for schedule in schedule_exists:
    if new_schedule_request.start_time<schedule.end_time and new_schedule_request.end_time>schedule.start_time:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="A schedule already exists for this doctor at your requestion time slot. Please update the existing schedule or create a new one with a valid time slot.")

  new_schedule=Schedule(**new_schedule_request.model_dump(),doctor_id=doctor.id)
  db.add(new_schedule)
  db.commit()



@router.put("/update_schedule/{schedule_id}",status_code=status.HTTP_204_NO_CONTENT)
def update_schedule(db:db_dependancy,user:user_dependancy,updated_schedule_request:ScheduleUpdateRequest,doctor:doctor_dependancy,schedule_id:int=Path(...,gt=0)):

  model=db.query(Schedule).filter(Schedule.schedule_id==schedule_id).filter(Schedule.doctor_id==doctor.id).first()
  if model is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Schedule not found for this doctor")
  
  if (updated_schedule_request.start_time is None and updated_schedule_request.end_time is not None) or (updated_schedule_request.start_time is not None and updated_schedule_request.end_time is None):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Both start_time and end_time must be provided together to update the schedule timings.")
  
  update_times=False
  if updated_schedule_request.start_time is not None and updated_schedule_request.end_time is not None:
    actual_start_time=updated_schedule_request.start_time
    actual_end_time=updated_schedule_request.end_time
    if actual_start_time >= actual_end_time:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="start_time must be before end_time")
    update_times=True
  else:
    actual_start_time=model.start_time
    actual_end_time=model.end_time

  if updated_schedule_request.day_of_week is not None:
    actual_day=updated_schedule_request.day_of_week
  else:
    actual_day=model.day_of_week
  schedule_exists=db.query(Schedule).filter(Schedule.doctor_id==doctor.id).filter(Schedule.day_of_week==actual_day).filter(Schedule.schedule_id!=schedule_id).all()
  for schedule in schedule_exists:
    if actual_start_time<schedule.end_time and actual_end_time>schedule.start_time:
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
def delete_schedule(db:db_dependancy,user:user_dependancy,doctor:doctor_dependancy,schedule_id:int=Path(...,gt=0)):

  model=db.query(Schedule).filter(Schedule.schedule_id==schedule_id).filter(Schedule.doctor_id==doctor.id).first()
  if model is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Schedule not found for this doctor")
  db.delete(model)
  db.commit()