from typing import Annotated
from fastapi import Depends, HTTPException,status
from sqlalchemy.orm import Session
from backend.models import PatientProfile,DoctorProfile
from ..database import get_db
from .auth import get_current_user

db_dependancy=Annotated[Session,Depends(get_db)]
user_dependancy=Annotated[dict,Depends(get_current_user)]

def get_current_active_patient(db:db_dependancy,user:user_dependancy):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")
  if (user.get('role')).lower()!="patient":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not allowed to access this endpoint because your role doesn't match.")
  profile_exists=db.query(PatientProfile).filter(PatientProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  return profile_exists


def get_current_active_doctor(db:db_dependancy,user:user_dependancy):
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication Failes")
  if (user.get('role')).lower()!="doctor":
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="You are not allowed to access this endpoint because your role doesn't match.")
  
  profile_exists=db.query(DoctorProfile).filter(DoctorProfile.user_id==user.get('id')).first()
  if not profile_exists:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Profile required to access this resource")
  return profile_exists