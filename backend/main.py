from fastapi import FastAPI
from .routers import appointments
from .database import Base,engine
from .routers import auth,patients,doctors,schedules

app=FastAPI()

app.include_router(appointments.router)
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(schedules.router)


Base.metadata.create_all(bind=engine)

@app.get("/healthy")
def health_check():
  return {"status":"healthy"}