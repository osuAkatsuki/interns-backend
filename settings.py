import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.environ["APP_ENV"]
APP_COMPONENT = os.environ["APP_COMPONENTS"]
APP_HOST = os.environ["APP_HOST"]
APP_PORT = int(os.environ["APP_PORT"])

DB_SCHEME = os.environ["DB_SCHEME"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]
