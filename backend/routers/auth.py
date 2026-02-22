from pydantic import BaseModel,Field
from fastapi import APIRouter,Depends,status,HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PatientProfile,Appointments,Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from jose import jwt ,JWTError
import hashlib

SECRET_KEY="8967e573b9c602d70e39901eca9ddb4dacb88dc61123fc87382e37b28699907c"
ALGORITHM="HS256"

oauth2_bearer=OAuth2PasswordBearer(tokenUrl="/auth/token")

bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

router=APIRouter(
  prefix="/auth",
  tags=["auth"]
)

db_dependancy=Annotated[Session,Depends(get_db)]

# class PatientCreateRequest(BaseModel):
#   username:str=Field(min_length=3,max_length=50)
#   password:str=Field(min_length=8)
#   firstname:str=Field(max_length=50)
#   lastname:str=Field(max_length=50)
#   age:int=Field(gt=0)
#   phone_number:int=Field(gt=0)
#   email:str

class UserCreateRequest(BaseModel):
  username:str=Field()
  email:str
  password:str
  role:str



class TokenResponse(BaseModel):
  access_token:str
  token_type:str


def get_current_user(token:Annotated[dict,Depends(oauth2_bearer)]):
  try:
    payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    
    username=payload.get('sub')
    user_id=payload.get('id')
    role=payload.get('role')
    if username is None or user_id is None:
      raise HTTPException(status_code=401,detail="Could not validate credentials")
  except JWTError:
    raise HTTPException(status_code=401,detail="Could not validate credentials")
  return {"username":username,"id":user_id,"role":role}



def authenticate_user(username:str,password:str,db:db_dependancy):
  user=db.query(Users).filter(Users.username==username).first()
  if user is None:
    return False
  if not bcrypt_context.verify(password,user.hashed_password):
    return False
  return True

def get_user_access_token(username:str,user_id:int,role:str,expire_delta:timedelta):
  payload={
    "sub":username,
    "id":user_id,
    "role":role
  }
  expires=datetime.now(timezone.utc)+expire_delta
  payload.update({"exp":expires})
  encoded_jwt=jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
  return encoded_jwt



# @router.post("/create_new_patient",status_code=status.HTTP_201_CREATED)
# def create_new_patient(db:db_dependancy,patient_create_request:PatientCreateRequest):
  
#   new_patient=PatientProfile(
#     username=patient_create_request.username,
#     hashed_password=bcrypt_context.hash(patient_create_request.password),
#     firstname=patient_create_request.firstname,
#     lastname=patient_create_request.lastname,
#     age=patient_create_request.age,
#     phone_number=patient_create_request.phone_number,
#     email=patient_create_request.email
#   )
#   db.add(new_patient)
#   db.commit()


@router.post("/create_new_user",status_code=status.HTTP_200_OK)
def create_new_user(db:db_dependancy,user_create_request:UserCreateRequest):
  new_user=Users(
    username=user_create_request.username,
    hashed_password=bcrypt_context.hash(user_create_request.password),
    email=user_create_request.email,
    role=user_create_request.role
  )
  db.add(new_user)
  db.commit()


@router.post("/token",status_code=status.HTTP_200_OK,response_model=TokenResponse)
def get_token(db:db_dependancy,form_data:Annotated[OAuth2PasswordRequestForm,Depends()]):
  authenticated_user=authenticate_user(form_data.username,form_data.password,db)
  if not authenticated_user:
    raise HTTPException(status_code=401,detail="Invalid credentials")
  user=db.query(Users).filter(Users.username==form_data.username).first()
  token=get_user_access_token(username=form_data.username,user_id=user.user_id,role=user.role,expire_delta=timedelta(minutes=20))
  
  return {"access_token":token,"token_type":"bearer"}
