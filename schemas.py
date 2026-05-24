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

class FCMTokenUpdate(BaseModel):
    fcm_token: s

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

# region Invitations & Audit
class InvitationCreate(BaseModel):
    department_id: Optional[int] = None
    position_id: Optional[int] = None


class InvitationResponse(BaseModel):
    id: int
    code: str
    company_id: int
    department_id: Optional[int]
    position_id: Optional[int]
    is_used: bool

    model_config = ConfigDict(from_attributes=True)


class JoinCompanyRequest(BaseModel):
    code: str


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str] = None
    action: str
    details: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm_custom(cls, log_obj):
        return cls(
            id=log_obj.id,
            user_id=log_obj.user_id,
            user_email=log_obj.user.email if log_obj.user else "Unknown",
            action=log_obj.action,
            details=log_obj.details,
            created_at=log_obj.created_at
        )
# endregion