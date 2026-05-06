# main.py
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
    return db.query(models.Task).filter(models.Task.user_id == current_user.id).all()


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

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted successfully"}
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