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
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None

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
    updated_at: datetime
    is_deleted: bool

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
    updated_at: datetime
    is_deleted: bool

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
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
#endregion

#region Sync
class SyncTaskItem(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    is_completed: bool
    is_deleted: bool
    updated_at: datetime

class SyncRequest(BaseModel):
    last_sync_at: Optional[datetime] = None
    tasks: list[SyncTaskItem] = []

class SyncResponse(BaseModel):
    current_sync_at: datetime
    tasks: list[TaskResponse]
#endregion

#region Company Structure
class CompanyCreate(BaseModel):
    name: str

class CompanyResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    name: str
    company_id: int

class DepartmentResponse(BaseModel):
    id: int
    name: str
    company_id: int
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class PositionCreate(BaseModel):
    name: str
    department_id: int

class PositionResponse(BaseModel):
    id: int
    name: str
    department_id: int
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
#endregion