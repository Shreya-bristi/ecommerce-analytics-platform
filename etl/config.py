import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_engine(schema: str):
    """Create a SQLAlchemy engine for the given schema."""
    return create_engine(
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{schema}"
    )