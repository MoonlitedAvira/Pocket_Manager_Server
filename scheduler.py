# scheduler.py
import asyncio
from datetime import datetime, timedelta, timezone
from database import SessionLocal
import models
import fcm


async def check_periodic_events_loop():
    while True:
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc).replace(tzinfo=None)

            three_days_later_start = now + timedelta(days=3)
            three_days_later_end = now + timedelta(days=3, hours=1)

            urgent_tasks = db.query(models.Task).filter(
                models.Task.deadline >= three_days_later_start,
                models.Task.deadline < three_days_later_end,
                models.Task.is_completed == False,
                models.Task.is_deleted == False
            ).all()

            for task in urgent_tasks:
                user_id = task.assigned_user_id or task.user_id
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user and user.fcm_token:
                    fcm.send_push(
                        token=user.fcm_token,
                        title="Горит дедлайн! 🔥",
                        body=f"До дедлайна по задаче '{task.title}' осталось 3 дня!"
                    )

            starting_tasks = db.query(models.Task).filter(
                models.Task.start_execution_at <= now,
                models.Task.start_execution_at > (now - timedelta(hours=1)),
                models.Task.is_completed == False,
                models.Task.is_deleted == False
            ).all()

            for task in starting_tasks:
                user_id = task.assigned_user_id or task.user_id
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user and user.fcm_token:
                    fcm.send_push(
                        token=user.fcm_token,
                        title="Пора за работу 🚀",
                        body=f"Наступило время исполнения задачи: {task.title}"
                    )

            current_time = datetime.now()
            if current_time.weekday() == 4 and current_time.hour == 15:
                users = db.query(models.User).filter(models.User.fcm_token != None).all()
                for user in users:
                    fcm.send_push(
                        token=user.fcm_token,
                        title="Итоги недели 📊",
                        body="Пятница! Пожалуйста, пройдите тесты Маслач и Мюнстерберга для оценки концентрации и выгорания."
                    )

            db.close()
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")

        await asyncio.sleep(3600)