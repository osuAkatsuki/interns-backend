import io
import secrets
from uuid import UUID
from uuid import uuid4

from PIL import Image

from server import logger
from server.adapters import s3
from server.errors import ServiceError
from server.repositories import screenshots


async def create(
    screenshot_data: bytes,
) -> screenshots.Screenshot | ServiceError:
    # validate screenshot is correct
    with io.BytesIO(screenshot_data) as file:
        try:
            screenshot = Image.open(file)
            screenshot.verify()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to parse screenshot file", exc_info=exc)
            return ServiceError.SCREENSHOTS_IMAGE_INVALID

    file_name = secrets.token_urlsafe(16)
    file_type = screenshot.format
    assert file_type in ("PNG", "JPEG")

    if file_type == "PNG":
        file_name += ".png"
        content_type = "image/png"
    elif file_type == "JPEG":
        file_name += ".jpg"
        content_type = "image/jpeg"
    else:
        logger.error("Screenshot uploaded with invalid file type", file_type=file_type)
        return ServiceError.SCREENSHOTS_IMAGE_INVALID

    # Upload to Amazon S3
    try:
        await s3.upload(
            screenshot_data,
            file_name,
            folder="screenshots",
            content_type=content_type,
            acl="public-read",
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    screenshot_download_url = s3.get_s3_public_url(
        bucket_name="osu-server-professing",
        file_path=f"screenshots/{file_name}",
    )

    # Store screenshot metadata in database
    try:
        screenshot_id = uuid4()
        screenshot = await screenshots.create(
            screenshot_id=screenshot_id,
            file_name=file_name,
            file_type=file_type,
            file_size=len(screenshot_data),
            download_url=screenshot_download_url,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    return screenshot


async def fetch_one(screenshot_id: UUID) -> screenshots.Screenshot | ServiceError:
    screenshot = await screenshots.fetch_one(screenshot_id)

    if screenshot is None:
        return ServiceError.SCREENSHOTS_NOT_FOUND

    return screenshot
