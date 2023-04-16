import os
from dotenv import load_dotenv

def read_bool(value: str) -> bool:
    return value.lower() == "true"

load_dotenv()

APP_ENV = os.environ["APP_ENV"]
APP_COMPONENT = os.environ["APP_COMPONENT"]
APP_HOST = os.environ["APP_HOST"]
APP_PORT = int(os.environ["APP_PORT"])

DB_SCHEME = os.environ["DB_SCHEME"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]
DB_USE_SSL = read_bool(os.environ["DB_USE_SSL"])
INITIALLY_AVAILABLE_DB = os.environ["INITIALLY_AVAILABLE_DB"]

REDIS_SCHEME = os.environ["REDIS_SCHEME"]
REDIS_USER = os.environ["REDIS_USER"]
REDIS_PASS = os.environ["REDIS_PASS"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_DB = int(os.environ["REDIS_DB"])
