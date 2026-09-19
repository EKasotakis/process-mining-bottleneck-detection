import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd


load_dotenv()


def get_engine():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    connection_string = (
        f"postgresql+psycopg2://"
        f"{user}:{password}@{host}:{port}/{database}"
    )

    return create_engine(connection_string)


def load_event_log_to_database(filepath):
    df = pd.read_csv(filepath)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    engine = get_engine()

    df.to_sql(
        "event_log",
        engine,
        if_exists="replace",
        index=False,
    )

    print(
        f"Loaded {len(df):,} events "
        f"into PostgreSQL table 'event_log'"
    )


def read_event_log():
    engine = get_engine()

    query = """
        SELECT *
        FROM event_log
        ORDER BY case_id, timestamp
    """

    return pd.read_sql(query, engine)


if __name__ == "__main__":
    load_event_log_to_database("data/raw/event_log.csv")