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

READ_DB_SCHEME = os.environ["READ_DB_SCHEME"]
READ_DB_HOST = os.environ["READ_DB_HOST"]
READ_DB_PORT = int(os.environ["READ_DB_PORT"])
READ_DB_USER = os.environ["READ_DB_USER"]
READ_DB_PASS = os.environ["READ_DB_PASS"]
READ_DB_NAME = os.environ["READ_DB_NAME"]
READ_DB_USE_SSL = read_bool(os.environ["READ_DB_USE_SSL"])
READ_DB_CA_CERTIFICATE_BASE64 = os.environ["READ_DB_CA_CERTIFICATE"]
INITIALLY_AVAILABLE_READ_DB = os.environ["INITIALLY_AVAILABLE_READ_DB"]

WRITE_DB_SCHEME = os.environ["WRITE_DB_SCHEME"]
WRITE_DB_HOST = os.environ["WRITE_DB_HOST"]
WRITE_DB_PORT = int(os.environ["WRITE_DB_PORT"])
WRITE_DB_USER = os.environ["WRITE_DB_USER"]
WRITE_DB_PASS = os.environ["WRITE_DB_PASS"]
WRITE_DB_NAME = os.environ["WRITE_DB_NAME"]
WRITE_DB_USE_SSL = read_bool(os.environ["WRITE_DB_USE_SSL"])
WRITE_DB_CA_CERTIFICATE_BASE64 = os.environ["WRITE_DB_CA_CERTIFICATE"]
INITIALLY_AVAILABLE_WRITE_DB = os.environ["INITIALLY_AVAILABLE_WRITE_DB"]

DB_POOL_MIN_SIZE = int(os.environ["DB_POOL_MIN_SIZE"])
DB_POOL_MAX_SIZE = int(os.environ["DB_POOL_MAX_SIZE"])

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
