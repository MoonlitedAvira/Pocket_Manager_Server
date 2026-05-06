# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
import models


#region ser
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: models.RoleEnum

    model_config = ConfigDict(from_attributes=True)
#endregion

#region Token
#Lmao region for 1 class
class Token(BaseModel):
    access_token: str
    token_type: str
#rergion

#region Task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
#endregion

#region Pomodoro
class PomodoroCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int


class PomodoroResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)
#endregion

#region SAN
class SanTestCreate(BaseModel):
    score_s: float
    score_a: float
    score_n: float


class SanTestResponse(BaseModel):
    id: int
    date: datetime
    score_s: float
    score_a: float
    score_n: float

    model_config = ConfigDict(from_attributes=True)
#endregion