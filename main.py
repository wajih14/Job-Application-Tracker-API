from fastapi import FastAPI

app = FastAPI()

applications = []

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/applications")
def get_applications():
    return applications