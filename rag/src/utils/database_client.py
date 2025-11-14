import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.db_url)
        return self._engine

    def read_sql(self, query: str, **kwargs) -> pd.DataFrame:
        with self.engine.connect() as connection:
            return pd.read_sql(query, connection, **kwargs)

    def write_df(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        index: bool = False,
        **kwargs,
    ):
        with self.engine.connect() as connection:
            df.to_sql(
                table_name,
                con=connection,
                if_exists=if_exists,
                index=index,
                **kwargs,
            )

    def execute_query(self, query: str):
        with self.engine.begin() as connection:
            connection.execute(text(query))

    def fetch_one(self, query: str):
        with self.engine.connect() as connection:
            result = connection.execute(text(query)).fetchone()
            return result

    def fetch_all(self, query: str):
        with self.engine.connect() as connection:
            result = connection.execute(text(query)).fetchall()
            return result

    def execute_scalar(self, query: str):
        with self.engine.connect() as connection:
            result = connection.execute(text(query)).scalar()
            return result

    def close(self):
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __del__(self):
        self.close()