from .utils import *
from fastapi import status
from backend.database import get_db
from backend.routers.auth import get_current_user

@pytest.fixture(autouse=True )
def set_doctor_profile():
  app.dependency_overrides[get_db]=override_get_db
  app.dependency_overrides[get_current_user]=override_get_current_doctor
  yield
  app.dependency_overrides.clear()

##### get_doctor_details_endpoint ###########
def test_get_doctor_details(users_db,profiles_db):
  response=client.get("/doctors/get_doctor_details")

  assert response.status_code==status.HTTP_200_OK
  assert response.json()=={"id":1,
                            "user_id":1,
                            "firstname":"Krishna",
                            "lastname":"Kumar",
                            "age":30,
                            "phone_number":"123456789",
                            "department":"orthopaedic"}

########## create_new_doctor_endpoint #########
def test_create_new_doctor(users_db):
  request_data={"firstname":"shravana",
                "lastname":"kumar",
                "age":29,
                "phone_number":"234567891",
                "department":"general"}
  response=client.post("/doctors/create_new_doctor",json=request_data)
  assert response.status_code==status.HTTP_201_CREATED

  db=TestLocalSession()
  model=db.query(DoctorProfile).filter(DoctorProfile.id==1).first()

  assert model.firstname=="shravana"
  assert model.user_id==1
  assert model.lastname=="kumar"
  assert model.age==29
  assert model.phone_number=="234567891"
  assert model.department=="general"


############## update_doctor_details_endpoint ##########
def test_update_doctor_details(profiles_db):
  request_data={"firstname":"shravana",
                "lastname":"kumar",
                "age":29,
                "phone_number":"234567891",
                "department":"general"}
  response=client.put("/doctors/update_doctor_details",json=request_data)
  assert response.status_code==status.HTTP_204_NO_CONTENT

  db=TestLocalSession()

  model=db.query(DoctorProfile).filter(DoctorProfile.user_id==1).first()
  assert model.firstname=="shravana"
  assert model.user_id==1
  assert model.lastname=="kumar"
  assert model.age==29
  assert model.phone_number=="234567891"
  assert model.department=="general"
