import os
import urllib.request

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
PARQUET_FILE = "yellow_tripdata_2024-01.parquet"


def setup_database(con):
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(PARQUET_FILE):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, PARQUET_FILE)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM '{PARQUET_FILE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Loaded {count} rows")
    return count


class SQLTools:
    def __init__(self, connection):
        self.connection = connection

    def execute_query(self, query):
        result = self.connection.execute(query).fetchall()
        return result
    
    def get_schema(self):
        """
        Runs DESCRIBE trips and returns all column names with their types
        """
        schema = self.connection.execute("DESCRIBE trips").fetchall()
        return schema

    def run_sql(self, query: str):
        """
        Executes a SQL query and returns results as text (column headers + data rows, limited to 50 rows)
        """
        query_result = self.connection.execute(query).fetchmany(50)
        return query_result
