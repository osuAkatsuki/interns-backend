import os

from dotenv import load_dotenv


def read_bool(value: str) -> bool:
    return value.lower() == "true"


load_dotenv()

APP_ENV = os.environ["APP_ENV"]
APP_COMPONENT = os.environ["APP_COMPONENT"]
APP_HOST = os.environ["APP_HOST"]
APP_PORT = int(os.environ["APP_PORT"])
APP_LOG_LEVEL = int(os.environ["APP_LOG_LEVEL"])

DB_SCHEME = os.environ["DB_SCHEME"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]
DB_USE_SSL = read_bool(os.environ["DB_USE_SSL"])
INITIALLY_AVAILABLE_DB = os.environ["INITIALLY_AVAILABLE_DB"]

REDIS_SCHEME = os.environ["REDIS_SCHEME"]
REDIS_PASS = os.environ["REDIS_PASS"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_DB = int(os.environ["REDIS_DB"])

OSU_API_V2_CLIENT_ID = os.environ["OSU_API_V2_CLIENT_ID"]
OSU_API_V2_CLIENT_SECRET = os.environ["OSU_API_V2_CLIENT_SECRET"]

S3_ACCESS_KEY_ID = os.environ["S3_ACCESS_KEY_ID"]
S3_SECRET_ACCESS_KEY = os.environ["S3_SECRET_ACCESS_KEY"]
S3_BUCKET_REGION = os.environ["S3_BUCKET_REGION"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_ENDPOINT_URL = os.environ["S3_ENDPOINT_URL"]
