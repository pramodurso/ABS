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


######## get_patient_details_endpoint ##########
def test_get_patient_details(users_db,profiles_db):
  response=client.get("/patients/get_patient_details")

  assert response.status_code==status.HTTP_200_OK
  assert response.json()=={"id":1,
                            "user_id":2,
                            "firstname":"Ashika",
                            "lastname":"Ranganath",
                            "age":28,
                            "phone_number":"987654321",}
  


###### create_new_patient_endpoint ###########
def test_create_new_patient(users_db):
  request_data={"firstname":"shravana",
                "lastname":"kumar",
                "age":29,
                "phone_number":"234567891"}
  response=client.post("/patients/create_new_patient",json=request_data)
  assert response.status_code==status.HTTP_201_CREATED

  db=TestLocalSession()
  model=db.query(PatientProfile).filter(PatientProfile.id==1).first()

  assert model.firstname=="shravana"
  assert model.user_id==2
  assert model.lastname=="kumar"
  assert model.age==29
  assert model.phone_number=="234567891"


######### update_patient_details_endpoint ########
def test_update_patient_details(profiles_db):
  request_data={"firstname":"shravana",
                "lastname":"kumar",
                "age":29,
                "phone_number":"234567891"}
  response=client.put("/patients/update_patient_details",json=request_data)
  assert response.status_code==status.HTTP_204_NO_CONTENT

  db=TestLocalSession()

  model=db.query(PatientProfile).filter(PatientProfile.user_id==2).first()
  assert model.firstname=="shravana"
  assert model.user_id==2
  assert model.lastname=="kumar"
  assert model.age==29
  assert model.phone_number=="234567891"


