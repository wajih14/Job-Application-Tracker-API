from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from uuid import UUID
from datetime import datetime

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    SEEKING_TO_APPLY = "seeking to apply"
    SPECIAL = "special"

class AppSubmit(BaseModel):
    company: str = Field(min_length=2, description="The name of the company")
    position: str = Field(min_length=2, description="The position applied for")
    status: ApplicationStatus

class StatusUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    id: int
    company: str
    position: str
    status: ApplicationStatus
    created_at: datetime
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    email: str
    logged_in: bool

class PasswordCheck(BaseModel):
    password: str

class UserSubmit(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str