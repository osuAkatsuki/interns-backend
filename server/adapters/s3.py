import clients
import settings


async def upload(body: bytes, filename: str, folder: str) -> None:
    resp = await clients.s3_client.put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME, Key=f"{folder}/{filename}", Body=body
    )
    return None


async def download(filename: str, folder: str) -> bytes:
    resp = await clients.s3_client.get_object(
        Bucket=settings.AWS_S3_BUCKET_NAME, Key=f"{folder}/{filename}"
    )
    return await resp["Body"].read()
