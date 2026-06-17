# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
import models


#region ser
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class RecoverRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: models.RoleEnum
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_custom(cls, user_obj):
        return cls(
            id=user_obj.id,
            email=user_obj.email,
            role=user_obj.role,
            company_id=user_obj.company_id,
            department_id=user_obj.department_id,
            position_id=user_obj.position_id,
            company_name=user_obj.company_name
        )
#endregion

class FCMTokenUpdate(BaseModel):
    fcm_token: str

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
    start_execution_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    department_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    start_execution_at: Optional[datetime]
    deadline: Optional[datetime]
    assigned_user_id: Optional[int]
    department_id: Optional[int]

    class Config:
        from_attributes = True
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

class MaslachCreate(BaseModel):
    emotional_exhaustion: float
    depersonalization: float
    personal_accomplishment: float

class MaslachResponse(BaseModel):
    id: int
    date: datetime
    emotional_exhaustion: float
    depersonalization: float
    personal_accomplishment: float

    model_config = ConfigDict(from_attributes=True)


class MunsterbergCreate(BaseModel):
    correct_words: int
    time_spent_seconds: int
    errors: int = 0

class MunsterbergResponse(BaseModel):
    id: int
    date: datetime
    correct_words: int
    time_spent_seconds: int
    errors: int = 0

    model_config = ConfigDict(from_attributes=True)

#region Sync
class SyncTaskItem(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    is_completed: bool
    is_deleted: bool
    updated_at: datetime
    start_execution_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    department_id: Optional[int] = None

class SyncAttendanceItem(BaseModel):
    id: Optional[int] = None
    date: datetime
    action_type: str
    updated_at: datetime
    is_deleted: bool

class SyncSanItem(BaseModel):
    id: Optional[int] = None
    date: datetime
    score_s: float
    score_a: float
    score_n: float
    updated_at: datetime
    is_deleted: bool

class SyncMaslachItem(BaseModel):
    id: Optional[int] = None
    date: datetime
    emotional_exhaustion: float
    depersonalization: float
    personal_accomplishment: float
    updated_at: datetime
    is_deleted: bool

class SyncMunsterbergItem(BaseModel):
    id: Optional[int] = None
    date: datetime
    correct_words: int
    time_spent_seconds: int
    errors: int
    updated_at: datetime
    is_deleted: bool

class SyncRequest(BaseModel):
    last_sync_at: Optional[datetime] = None
    tasks: list[SyncTaskItem] = []
    attendances: list[SyncAttendanceItem] = []
    san_results: list[SyncSanItem] = []
    maslach_results: list[SyncMaslachItem] = []
    munsterberg_results: list[SyncMunsterbergItem] = []

class SyncResponse(BaseModel):
    current_sync_at: datetime
    tasks: list[TaskResponse] = []
    attendances: list['AttendanceResponse'] = []
    san_results: list[SanTestResponse] = []
    maslach_results: list[MaslachResponse] = []
    munsterberg_results: list[MunsterbergResponse] = []
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


class PositionCreate(BaseModel):
    name: str
    department_id: int
    hierarchy_level: int = 0
    schedule_type: Optional[str] = "none"
    schedule_start: Optional[time] = None
    schedule_end: Optional[time] = None
    schedule_norm_minutes: Optional[int] = None

class PositionResponse(BaseModel):
    id: int
    name: str
    department_id: int
    hierarchy_level: int
    schedule_type: str = "none"
    schedule_start: Optional[time] = None
    schedule_end: Optional[time] = None
    schedule_norm_minutes: Optional[int] = None
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
    positions: list[PositionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class PositionUpdate(BaseModel):
    name: Optional[str] = None
    hierarchy_level: Optional[int] = None
    schedule_type: Optional[str] = None
    schedule_start: Optional[time] = None
    schedule_end: Optional[time] = None
    schedule_norm_minutes: Optional[int] = None

class WorkerUpdate(BaseModel):
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    role: Optional[models.RoleEnum] = None

class WorkerStatsResponse(BaseModel):
    user_id: int
    san_results: list[SanTestResponse] = []
    maslach_results: list[MaslachResponse] = []
    munsterberg_results: list[MunsterbergResponse] = []
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

class AttendanceCreate(BaseModel):
    action_type: str = "check_in"

class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    date: datetime
    action_type: str
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)