import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE positions ADD COLUMN schedule_days VARCHAR(50) DEFAULT NULL;"))
        conn.commit()
        print("Schedule days column added successfully")
    except Exception as e:
        print(f"Error: {e}")
