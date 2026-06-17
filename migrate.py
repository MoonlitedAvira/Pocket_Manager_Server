import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE positions ADD COLUMN schedule_type VARCHAR(50) DEFAULT 'none';"))
        conn.execute(text("ALTER TABLE positions ADD COLUMN schedule_start TIME;"))
        conn.execute(text("ALTER TABLE positions ADD COLUMN schedule_end TIME;"))
        conn.execute(text("ALTER TABLE positions ADD COLUMN schedule_norm_minutes INTEGER;"))
        conn.commit()
        print("Migration successful")
    except Exception as e:
        print(f"Error: {e}")
