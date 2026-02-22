from fastapi import APIRouter,status,Depends,HTTPException
from pydantic import BaseModel,Field
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PatientProfile
from .auth import get_current_user

router=APIRouter(
  prefix="/patients",
  tags=["patients"]
)

db_dependancy=Annotated[Session,Depends(get_db)]
user_dependancy=Annotated[dict,Depends(get_current_user)]

class PatientCreateRequest(BaseModel):
  firstname:str=Field(max_length=50)
  lastname:str=Field(max_length=50)
  age:int=Field(gt=0)
  phone_number:int=Field(gt=0)

class PatientUpdateRequest(BaseModel):
  firstname:Optional[str]=Field(default=None,min_length=1)
  lastname:Optional[str]=Field(default=None,min_length=1)
  age:Optional[int]=Field(default=None)
  phone_number:Optional[int]=Field(gt=0)



@router.get("/get_patient_details",status_code=status.HTTP_200_OK)
def get_patient_details(db:db_dependancy,user:user_dependancy):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  return db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()

@router.post("/create_new_patient",status_code=status.HTTP_201_CREATED)
def create_new_patient(db:db_dependancy,user:user_dependancy,create_patient_request:PatientCreateRequest):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed") 
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  exist=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if exist:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"A profile already exists with user_id {user.get('id')}")

  new_patient=PatientProfile(
    user_id=user.get('id'),
    firstname=create_patient_request.firstname,
    lastname=create_patient_request.lastname,
    age=create_patient_request.age,
    phone_number=create_patient_request.phone_number
  )
  db.add(new_patient)
  db.commit()

@router.put("/update_patient_details",status_code=status.HTTP_204_NO_CONTENT)
def update_patient_details(db:db_dependancy,user:user_dependancy,update_patient_request:PatientUpdateRequest):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  
  model=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if model is None: 
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  
  if update_patient_request.firstname is not None:
    model.firstname=update_patient_request.firstname
  if update_patient_request.lastname is not None:
    model.lastname=update_patient_request.lastname
  if update_patient_request.age is not None:
    model.age=update_patient_request.age
  if update_patient_request.phone_number is not None:
    model.phone_number=update_patient_request.phone_number

  db.commit()
  

