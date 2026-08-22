from pydantic import BaseModel

class AppSubmit(BaseModel):
    company: str
    position: str
    status: str

class StatusUpdate(BaseModel):
    status: str