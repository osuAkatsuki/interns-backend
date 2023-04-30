import botocore.exceptions

from server import clients
from server import logger
from server import settings


async def upload(body: bytes, filename: str, folder: str) -> None:
    try:
        await clients.s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=f"{folder}/{filename}",
            Body=body,
        )
    except botocore.exceptions.BotoCoreError as exc:
        logger.error("Failed to upload file to S3", exc_info=exc)
        return None

    return None


async def download(filename: str, folder: str) -> bytes | None:
    try:
        response = await clients.s3_client.get_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=f"{folder}/{filename}",
        )
    except botocore.exceptions.BotoCoreError as exc:
        logger.error("Failed to download file from S3", exc_info=exc)
        return None

    return await response["Body"].read()


def get_s3_public_url(bucket_name: str, file_path: str) -> str:
    return f"https://{bucket_name}.s3.amazonaws.com/{file_path}"
