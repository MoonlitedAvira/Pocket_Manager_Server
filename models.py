# models.py
import enum
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text, DateTime, Enum, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class SyncMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        default=False
    )

class RoleEnum(enum.Enum):
    self_employed = "self_employed"
    worker = "worker"
    manager = "manager"
    director = "director"

class User(Base, SyncMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.self_employed)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    fcm_token: Mapped[str] = mapped_column(String(255), nullable=True)

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        "Task", 
        back_populates="user", 
        foreign_keys="[Task.user_id]", 
        cascade="all, delete-orphan"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task", 
        back_populates="assigned_user", 
        foreign_keys="[Task.assigned_user_id]", 
        cascade="all, delete-orphan"
    )
    pomodoros: Mapped[list["PomodoroSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    san_results: Mapped[list["SanTestResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    maslach_results: Mapped[list["MaslachResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    munsterberg_results: Mapped[list["MunsterbergResult"]] = relationship(back_populates="user",
                                                                          cascade="all, delete-orphan")

    company: Mapped["Company"] = relationship(back_populates="users", foreign_keys=[company_id])
    department: Mapped["Department"] = relationship(back_populates="users", foreign_keys=[department_id])
    position: Mapped["Position"] = relationship(back_populates="users", foreign_keys=[position_id])

    @property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None

#region Company Structure
class Company(Base, SyncMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    departments: Mapped[list["Department"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="company", foreign_keys="[User.company_id]")


class Department(Base, SyncMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="departments")
    positions: Mapped[list["Position"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="department")


class Position(Base, SyncMixin):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    department: Mapped["Department"] = relationship(back_populates="positions")
    users: Mapped[list["User"]] = relationship(back_populates="position")
#endregion


class Task(Base, SyncMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    start_execution_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    assigned_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=True)

    user: Mapped["User"] = relationship(
        "User", 
        back_populates="tasks", 
        foreign_keys=[user_id]
    )
    assigned_user: Mapped["User"] = relationship(
        "User", 
        back_populates="assigned_tasks", 
        foreign_keys=[assigned_user_id]
    )
    department: Mapped["Department"] = relationship()

class PomodoroSession(Base, SyncMixin):
    __tablename__ = "pomodoro_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship(back_populates="pomodoros")

class SanTestResult(Base, SyncMixin):
    __tablename__ = "san_test_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    score_s: Mapped[float] = mapped_column(nullable=False)
    score_a: Mapped[float] = mapped_column(nullable=False)
    score_n: Mapped[float] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="san_results")


class MaslachResult(Base, SyncMixin):
    __tablename__ = "maslach_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Три шкалы выгорания по Маслач
    emotional_exhaustion: Mapped[float] = mapped_column(nullable=False)
    depersonalization: Mapped[float] = mapped_column(nullable=False)
    personal_accomplishment: Mapped[float] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="maslach_results")


class MunsterbergResult(Base, SyncMixin):
    __tablename__ = "munsterberg_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    correct_words: Mapped[int] = mapped_column(nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(nullable=False)
    errors: Mapped[int] = mapped_column(Integer, server_default="0", default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="munsterberg_results")

#region Invitations & Audit
class Invitation(Base, SyncMixin):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship()
#endregion

class Attendance(Base, SyncMixin):
    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    action_type: Mapped[str] = mapped_column(String(50), default="check_in")

    user: Mapped["User"] = relationship()