from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Application(BaseModel):
    company: str
    position: str
    status: str

applications = []

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/applications")
def get_applications():
    return applications

@app.post("/applications")
def create_application(application: Application):
    applications.append(application)
    return application