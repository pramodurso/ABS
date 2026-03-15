from fastapi import APIRouter,status,Depends,HTTPException
from pydantic import BaseModel,Field
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DoctorProfile
from .auth import get_current_user
from .dependencies import get_current_active_doctor

router=APIRouter(
  prefix="/doctors",
  tags=["doctors"]
)

db_dependancy=Annotated[Session,Depends(get_db)]
user_dependancy=Annotated[dict,Depends(get_current_user)]

doctor_dependancy=Annotated[DoctorProfile,Depends(get_current_active_doctor)]

class DoctorCreateRequest(BaseModel):
  firstname:str=Field(max_length=50)
  lastname:str=Field(max_length=50)
  age:int=Field(gt=0)
  phone_number:int=Field(gt=0)
  department:str

class DoctorUpdateRequest(BaseModel):
  firstname:Optional[str]=Field(default=None,min_length=1)
  lastname:Optional[str]=Field(default=None,min_length=1)
  age:Optional[int]=Field(default=None)
  phone_number:Optional[int]=Field(default=None,gt=0)
  department:Optional[str]=Field(default=None)



@router.get("/get_doctor_details",status_code=status.HTTP_200_OK)
def get_doctor_details(db:db_dependancy,user:user_dependancy,doctor:doctor_dependancy):
  return doctor

@router.post("/create_new_doctor",status_code=status.HTTP_201_CREATED)
def create_new_doctor(db:db_dependancy,user:user_dependancy,create_doctor_request:DoctorCreateRequest):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed") 
  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  exist=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if exist:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"A profile already exists with user_id {user.get('id')}")

  new_doctor=DoctorProfile(
    user_id=user.get('id'),
    firstname=create_doctor_request.firstname,
    lastname=create_doctor_request.lastname,
    age=create_doctor_request.age,
    phone_number=create_doctor_request.phone_number,
    department=create_doctor_request.department
  )
  db.add(new_doctor)
  db.commit()

@router.put("/update_doctor_details",status_code=status.HTTP_204_NO_CONTENT)
def update_doctor_details(db:db_dependancy,user:user_dependancy,update_doctor_request:DoctorUpdateRequest,doctor:doctor_dependancy):
  
  if update_doctor_request.firstname is not None:
    doctor.firstname=update_doctor_request.firstname
  if update_doctor_request.lastname is not None:
    doctor.lastname=update_doctor_request.lastname
  if update_doctor_request.age is not None:
    doctor.age=update_doctor_request.age
  if update_doctor_request.phone_number is not None:
    doctor.phone_number=update_doctor_request.phone_number
  if update_doctor_request.department is not None:
    doctor.department=update_doctor_request.department

  db.commit()