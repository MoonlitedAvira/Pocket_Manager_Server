import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE positions ADD COLUMN permissions VARCHAR(255) DEFAULT NULL;"))
        conn.commit()
        print("Permissions column added successfully")
    except Exception as e:
        print(f"Error: {e}")
