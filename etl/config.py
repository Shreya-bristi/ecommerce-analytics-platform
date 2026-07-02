import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

load_dotenv()

def get_engine(schema: str):
    """Create a SQLAlchemy engine for the given schema."""
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        database=schema,
    )
    return create_engine(url)