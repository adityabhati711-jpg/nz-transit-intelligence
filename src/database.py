from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from src.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def test_database_connection():
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database();")
        ).scalar()

        postgres_version = connection.execute(
            text("SELECT version();")
        ).scalar()

        print("DATABASE CONNECTION SUCCESSFUL")
        print("------------------------------")
        print("Database:", database_name)
        print("PostgreSQL:", postgres_version)


if __name__ == "__main__":
    test_database_connection()