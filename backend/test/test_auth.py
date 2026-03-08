from .utils import *
from backend.database import get_db
from datetime import timedelta
from backend.routers.auth import get_user_access_token,authenticate_user,get_current_user,ALGORITHM,SECRET_KEY
from jose import jwt
from fastapi import status


@pytest.fixture(autouse=True )
def set_doctor_profile():
  app.dependency_overrides[get_db]=override_get_db
  app.dependency_overrides[get_current_user]=override_get_current_doctor
  yield
  app.dependency_overrides.clear()


####### authenticate_user_endpoint ########
def authenticated_user(users_db):
  db=TestLocalSession()

  authenticated_user=authenticate_user(username="krishnakumar",  password="iamdoctor",db=db)
  assert authenticated_user is True

  non_authenticated_user=authenticate_user(username="praveen",password="iamdoctor",db=db)
  assert non_authenticated_user is False

  wrong_password_user=authenticate_user(username="krishnakumar",password="viratkohli",db=db)
  assert wrong_password_user is False


###### get_get_user_access_token endpoint ########
def test_get_user_access_token():
  username="pramodurso"
  user_id=1
  role="doctor"
  expire_delta=timedelta(days=1)
  token=get_user_access_token(username,user_id,role,expire_delta)

  decoded_token=jwt.decode(token,algorithms=ALGORITHM,key=SECRET_KEY)

  assert decoded_token['sub']==username
  assert decoded_token['id']==user_id
  assert decoded_token['role']==role


##### get_current_user_endpoint #####
def test_get_current_user():
  username="pramodurso"
  user_id=1
  role="doctor"
  expire_delta=timedelta(days=1)
  token=get_user_access_token(username,user_id,role,expire_delta)

  response=get_current_user(token)

  assert response["username"]==username
  assert response["id"]==user_id
  assert response['role']==role



