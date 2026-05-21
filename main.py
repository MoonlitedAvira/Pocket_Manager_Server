# main.py
from datetime import timezone, datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from database import engine, Base, get_db
import models, schemas, security

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pocket Manager API")




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
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm использует поле username по стандарту, мы передаем туда email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
#endregion

#region To-Do List
@app.post("/tasks", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(security.get_current_user)):
    new_task = models.Task(**task.model_dump(), user_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
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
# endregion