from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
import json


app = FastAPI()

templates = Jinja2Templates(directory = "templates")

class Application(BaseModel):
    company: str
    position: str
    status: str

with open("test_data.json") as file:
    applications = json.load(file)

id = 4

@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"applications": applications, "title": "Home"})

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

@app.delete("/applications/{application_id}")
def delete_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            applications.remove(application)
            return {"message": "Application deleted"}
    raise HTTPException(status_code=404, detail = "Application not found")
    