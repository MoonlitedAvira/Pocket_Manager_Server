# main.py
import asyncio
import secrets
import fcm

from datetime import timezone, datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List
from database import engine, Base, get_db
from contextlib import asynccontextmanager

import models, schemas, security, fcm, scheduler
from datetime import timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# cd Pocket_Manager_Server
# . .venv/bin/activate
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# tail -f /var/log/pocketmanager.log

def cleanup_deleted_accounts():
    from database import SessionLocal
    db = SessionLocal()
    try:
        six_months_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=180)
        users_to_delete = db.query(models.User).filter(
            models.User.is_deleted == True,
            models.User.updated_at < six_months_ago
        ).all()
        for user in users_to_delete:
            db.delete(user)
        db.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(scheduler.check_periodic_events_loop())
    
    apscheduler = AsyncIOScheduler()
    apscheduler.add_job(cleanup_deleted_accounts, 'cron', hour=0, minute=0)
    apscheduler.start()
    
    yield

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pocket Manager API", lifespan=lifespan)




@app.get("/")
def read_root():
    return {"status": "Database and API are running!"}


#region reg&auth
@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return schemas.UserResponse.from_orm_custom(new_user)


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm использует поле username по стандарту, мы передаем туда email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    if user.is_deleted:
        raise HTTPException(status_code=403, detail="Account is deleted. Restoration available.")

    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/recover", response_model=schemas.Token)
def recover_user(req: schemas.RecoverRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not security.verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not deleted")
        
    user.is_deleted = False
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.delete("/users/me")
def delete_user(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    current_user.is_deleted = True
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"detail": "User marked as deleted"}

@app.get("/users/me", response_model=schemas.UserResponse)
def get_user_me(current_user: models.User = Depends(security.get_current_user)):
    return schemas.UserResponse.from_orm_custom(current_user)

@app.post("/users/attendance", response_model=schemas.AttendanceResponse)
def check_in(att_data: schemas.AttendanceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    new_att = models.Attendance(user_id=current_user.id, action_type=att_data.action_type)
    db.add(new_att)
    db.commit()
    db.refresh(new_att)
    return new_att

@app.get("/users/attendance", response_model=List[schemas.AttendanceResponse])
def get_attendance(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id).all()
#endregion

# region FCM Notifications
@app.put("/users/fcm-token")
def update_fcm_token(token_data: schemas.FCMTokenUpdate, db: Session = Depends(get_db),
                     current_user: models.User = Depends(security.get_current_user)):
    current_user.fcm_token = token_data.fcm_token
    db.commit()
    return {"status": "success", "detail": "FCM token updated"}


@app.post("/notifications/test")
def test_notification(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if not current_user.fcm_token:
        raise HTTPException(status_code=400, detail="FCM token not set for user")

    success = fcm.send_push(
        token=current_user.fcm_token,
        title="Pocket Manager",
        body="Второй этап успешно завершен! Уведомления работают.",
        data={"action": "test_push"}
    )

    if success:
        return {"status": "success", "detail": "Notification sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")


# endregion

#region To-Do List
@app.post("/tasks", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(security.get_current_user)):
    new_task = models.Task(**task.model_dump(), user_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    if new_task.assigned_user_id:
        worker = db.query(models.User).filter(models.User.id == new_task.assigned_user_id).first()
        if worker and worker.fcm_token:
            fcm.send_push(
                token=worker.fcm_token,
                title="Новая задача 📝",
                body=f"Руководитель назначил вам задачу: {new_task.title}",
                data={"task_id": str(new_task.id)}
            )

    elif new_task.department_id:
        workers = db.query(models.User).filter(
            models.User.department_id == new_task.department_id,
            models.User.id != current_user.id
        ).all()
        for worker in workers:
            if worker.fcm_token:
                fcm.send_push(
                    token=worker.fcm_token,
                    title="Новая задача отдела 👥",
                    body=f"В вашем отделе появилась задача: {new_task.title}",
                    data={"task_id": str(new_task.id)}
                )

    return new_task


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.Task).filter(
        or_(
            and_(models.Task.user_id == current_user.id, models.Task.assigned_user_id == None, models.Task.department_id == None),
            models.Task.assigned_user_id == current_user.id,
            and_(models.Task.department_id == current_user.department_id, current_user.department_id != None)
        ),
        models.Task.is_deleted == False
    ).all()

@app.get("/tasks/delegated", response_model=List[schemas.TaskResponse])
def get_delegated_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in [models.RoleEnum.manager, models.RoleEnum.director]:
        raise HTTPException(status_code=403, detail="Only managers can see delegated tasks")
    return db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        or_(models.Task.assigned_user_id != None, models.Task.department_id != None),
        models.Task.is_deleted == False
    ).all()


@app.put("/tasks/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(security.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_completed = True
    db.commit()
    db.refresh(task)
    return task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_data: schemas.TaskCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(security.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = task_data.title
    task.description = task_data.description
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(security.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_deleted = True
    db.commit()

    return {"detail": "Task marked as deleted"}
#endregion

#region Pomodoro
@app.post("/pomodoro", response_model=schemas.PomodoroResponse)
def save_pomodoro(session_data: schemas.PomodoroCreate, db: Session = Depends(get_db),
                  current_user: models.User = Depends(security.get_current_user)):
    new_session = models.PomodoroSession(**session_data.model_dump(), user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session
#endregion

#region san
@app.post("/san-test", response_model=schemas.SanTestResponse)
def save_san_test(test_data: schemas.SanTestCreate, db: Session = Depends(get_db),
                  current_user: models.User = Depends(security.get_current_user)):
    new_test = models.SanTestResult(**test_data.model_dump(), user_id=current_user.id)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test

@app.get("/san-test", response_model=List[schemas.SanTestResponse])
def get_san_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Получаем все результаты текущего пользователя, сортируем по убыванию даты (свежие сверху)
    results = db.query(models.SanTestResult)\
        .filter(models.SanTestResult.user_id == current_user.id)\
        .order_by(models.SanTestResult.date.desc())\
        .all()
    return results
#endregion

@app.post("/maslach-test", response_model=schemas.MaslachResponse)
def save_maslach_test(test_data: schemas.MaslachCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    new_test = models.MaslachResult(**test_data.model_dump(), user_id=current_user.id)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test

@app.get("/maslach-test", response_model=List[schemas.MaslachResponse])
def get_maslach_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    results = db.query(models.MaslachResult)\
        .filter(models.MaslachResult.user_id == current_user.id)\
        .order_by(models.MaslachResult.date.desc())\
        .all()
    return results

@app.post("/munsterberg-test", response_model=schemas.MunsterbergResponse)
def save_munsterberg_test(test_data: schemas.MunsterbergCreate, db: Session = Depends(get_db),
                         current_user: models.User = Depends(security.get_current_user)):
    new_test = models.MunsterbergResult(**test_data.model_dump(), user_id=current_user.id)
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test

@app.get("/munsterberg-test", response_model=List[schemas.MunsterbergResponse])
def get_munsterberg_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    results = db.query(models.MunsterbergResult)\
        .filter(models.MunsterbergResult.user_id == current_user.id)\
        .order_by(models.MunsterbergResult.date.desc())\
        .all()
    return results

# region Sync
@app.post("/sync", response_model=schemas.SyncResponse)
def sync_data(sync_req: schemas.SyncRequest, db: Session = Depends(get_db),
              current_user: models.User = Depends(security.get_current_user)):
    now = datetime.now(timezone.utc)

    for client_task in sync_req.tasks:
        client_time = client_task.updated_at.replace(tzinfo=None)

        if client_task.id:
            db_task = db.query(models.Task).filter(
                models.Task.id == client_task.id,
                models.Task.user_id == current_user.id
            ).first()

            if db_task:
                if client_time > db_task.updated_at:
                    db_task.title = client_task.title
                    db_task.description = client_task.description
                    db_task.is_completed = client_task.is_completed
                    db_task.is_deleted = client_task.is_deleted
        else:
            new_task = models.Task(
                user_id=current_user.id,
                title=client_task.title,
                description=client_task.description,
                is_completed=client_task.is_completed,
                is_deleted=client_task.is_deleted
            )
            db.add(new_task)

    db.commit()

    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)

    if sync_req.last_sync_at:
        last_sync_naive = sync_req.last_sync_at.replace(tzinfo=None)
        query = query.filter(models.Task.updated_at > last_sync_naive)

    server_tasks = query.all()

    return {
        "current_sync_at": now,
        "tasks": server_tasks
    }
# endregion

# region Company Management
@app.post("/companies", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(security.get_current_user)):
    if current_user.company_id is not None:
        raise HTTPException(status_code=400, detail="User is already in a company")

    new_company = models.Company(name=company.name, owner_id=current_user.id)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    current_user.role = models.RoleEnum.manager
    current_user.company_id = new_company.id
    db.commit()

    return new_company


@app.post("/departments", response_model=schemas.DepartmentResponse)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    if current_user.role != models.RoleEnum.manager or current_user.company_id != dept.company_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    new_dept = models.Department(**dept.model_dump())
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept


@app.post("/positions", response_model=schemas.PositionResponse)
def create_position(pos: schemas.PositionCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    department = db.query(models.Department).filter(models.Department.id == pos.department_id).first()
    if not department or department.company_id != current_user.company_id or current_user.role != models.RoleEnum.manager:
        raise HTTPException(status_code=403, detail="Not enough permissions or department not found")

    new_pos = models.Position(**pos.model_dump())
    db.add(new_pos)
    db.commit()
    db.refresh(new_pos)
    return new_pos

@app.get("/departments", response_model=List[schemas.DepartmentResponse])
def get_departments(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if not current_user.company_id:
        return []
    return db.query(models.Department).filter(models.Department.company_id == current_user.company_id).all()

@app.get("/users", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if not current_user.company_id:
        return []
    users = db.query(models.User).filter(models.User.company_id == current_user.company_id).all()
    return [schemas.UserResponse.from_orm_custom(u) for u in users]
# endregion

# region Invitations & Audit Endpoints

@app.post("/companies/invitations", response_model=schemas.InvitationResponse)
def create_invitation(inv_data: schemas.InvitationCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    if current_user.role != models.RoleEnum.manager:
        raise HTTPException(status_code=403, detail="Only managers can create invitations")

    invite_code = secrets.token_hex(4).upper()

    new_invite = models.Invitation(
        code=invite_code,
        company_id=current_user.company_id,
        department_id=inv_data.department_id,
        position_id=inv_data.position_id
    )
    db.add(new_invite)

    log_entry = models.AuditLog(
        company_id=current_user.company_id,
        user_id=current_user.id,
        action="CREATE_INVITATION",
        details=f"Created invitation code {invite_code} for dept_id {inv_data.department_id}"
    )
    db.add(log_entry)

    db.commit()
    db.refresh(new_invite)
    return new_invite

@app.delete("/companies/invitations/{code}")
def delete_invitation(code: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role != models.RoleEnum.manager:
        raise HTTPException(status_code=403, detail="Only managers can delete invitations")
    invite = db.query(models.Invitation).filter(models.Invitation.code == code.upper(), models.Invitation.company_id == current_user.company_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    db.delete(invite)
    db.commit()
    return {"detail": "Invitation deleted"}


@app.post("/companies/join")
def join_company(join_req: schemas.JoinCompanyRequest, db: Session = Depends(get_db),
                 current_user: models.User = Depends(security.get_current_user)):
    if current_user.company_id is not None:
        raise HTTPException(status_code=400, detail="You are already a member of a company")

    invite = db.query(models.Invitation).filter(
        models.Invitation.code == join_req.code.strip().upper(),
        models.Invitation.is_used == False
    ).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation code")

    current_user.role = models.RoleEnum.worker
    current_user.company_id = invite.company_id
    current_user.department_id = invite.department_id
    current_user.position_id = invite.position_id

    invite.is_used = True

    log_entry = models.AuditLog(
        company_id=invite.company_id,
        user_id=current_user.id,
        action="EMPLOYEE_JOINED",
        details=f"User {current_user.email} joined company using code {invite.code}"
    )
    db.add(log_entry)

    db.commit()
    return {"status": "success", "detail": f"Successfully joined company ID {invite.company_id}"}


@app.get("/companies/audit-logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in [models.RoleEnum.manager, models.RoleEnum.director]:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = db.query(models.AuditLog).filter(
        models.AuditLog.company_id == current_user.company_id
    ).order_by(models.AuditLog.created_at.desc()).all()

    return [schemas.AuditLogResponse.from_orm_custom(log) for log in logs]

# endregion

# region Debug Endpoints
from sqlalchemy import text

@app.post("/debug/clear-users")
def debug_clear_users(secret: str, db: Session = Depends(get_db)):
    if secret != "debug123":
        raise HTTPException(status_code=403, detail="Forbidden")

    db.execute(text("TRUNCATE TABLE users, companies CASCADE"))
    db.commit()
    return {"status": "success", "detail": "All users and related data deleted"}

@app.post("/debug/clear-timers")
def debug_clear_timers(secret: str, db: Session = Depends(get_db)):
    if secret != "debug123":
        raise HTTPException(status_code=403, detail="Forbidden")
    db.execute(text("TRUNCATE TABLE pomodoro_sessions CASCADE"))
    db.commit()
    return {"status": "success", "detail": "All timers deleted"}

@app.post("/debug/clear-tasks")
def debug_clear_tasks(secret: str, db: Session = Depends(get_db)):
    if secret != "debug123":
        raise HTTPException(status_code=403, detail="Forbidden")
    db.execute(text("TRUNCATE TABLE tasks CASCADE"))
    db.commit()
    return {"status": "success", "detail": "All tasks deleted"}
# endregion