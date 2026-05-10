import dotenv
import duckdb
import pytest

import patch_agent
from cost_tracker import display_total_usage, reset_cost_file
from sql_agent import create_agent, SQLAgentConfig
from sql_tools import SQLTools

dotenv.load_dotenv()
DB_PATH = "/Users/wesley/workspace/learning/ai-engineering-buildcamp/04-testing/homework/taxi.db"

def pytest_sessionstart(session):
    reset_cost_file()

def pytest_sessionfinish(session, exitstatus):
    display_total_usage()


@pytest.fixture(scope="session")
def db_connection():
    """
    Database connection is created once for the entire test run, not recreated for every test
    """
    con = duckdb.connect(DB_PATH, read_only=True)
    return con


@pytest.fixture(scope="module")
def agent(db_connection):
    agent_config = SQLAgentConfig()
    search_tools = SQLTools(connection=db_connection)
    return create_agent(agent_config, search_tools=search_tools)