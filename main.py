from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json


app = FastAPI()

class Application(BaseModel):
    company: str
    position: str
    status: str

class StatusUpdate(BaseModel):
    status: str

with open("test_data.json") as file:
    applications = json.load(file)

id = 4

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/applications")
def get_applications():
    return applications

@app.post("/applications")
def create_application(application: Application):
    global id
    application = {"id": id, **application.model_dump()}
    id += 1
    applications.append(application)
    return application

@app.get("/applications/{application_id}")
def get_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            return application
    raise HTTPException(status_code=404, detail = "Application not found")

@app.delete("/applications/{application_id}")
def delete_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            applications.remove(application)
            return {"message": "Application deleted"}
    raise HTTPException(status_code=404, detail = "Application not found")

@app.put("/applications/{application_id}")
def update_application_full(application_id: int, new_application_data: Application):
    for application in applications:
        if application["id"] == application_id:
            application["company"] = new_application_data.company
            application["position"] = new_application_data.position
            application["status"] = new_application_data.status
            return application
            
    raise HTTPException(status_code=404, detail = "Application not found")

@app.patch("/applications/{application_id}")
def update_application_status(application_id: int, new_status: StatusUpdate):
    for application in applications:
        if application["id"] == application_id:
            application["status"] = new_status.status
            return {"status": new_status}
    raise HTTPException(status_code = 404, detail = "Application not found")

