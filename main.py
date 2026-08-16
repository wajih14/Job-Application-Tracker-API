from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Application(BaseModel):
    company: str
    position: str
    status: str

applications = []
id = 1

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/applications")
def get_applications():
    return applications

@app.post("/applications")
def create_application(application: Application):
    global id
    application = {"id": id, **application.dict()}
    id += 1
    applications.append(application)
    return application

@app.get("/applications/{application_id}")
def get_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            return application
    raise HTTPException(status_code=404, detail = "Application not found")

