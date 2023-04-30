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

    # TODO: extension name? (e.g. png, jpg)
    screenshot_name = secrets.token_urlsafe(16)
    screenshot_type = screenshot.format
    assert screenshot_type is not None

    # Upload to Amazon S3
    try:
        await s3.upload(screenshot_data, screenshot_name, "screenshots")
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    screenshot_download_url = s3.get_s3_public_url(
        bucket_name="osu-server-professing",
        file_path=f"screenshots/{screenshot_name}",
    )

    # Store screenshot metadata in database
    try:
        screenshot_id = uuid4()
        screenshot = await screenshots.create(
            screenshot_id=screenshot_id,
            file_name=screenshot_name,
            file_type=screenshot_type,
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
