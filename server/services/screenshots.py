from typing import Any
from uuid import UUID, uuid4
from server.errors import ServiceError
from PIL import Image
import io
from server import logger
from server.adapters import s3

import secrets
from server.repositories import screenshots


async def create(
    screenshot_data: bytes,
) -> screenshots.Screenshot | ServiceError:
    # Read raw bytes
    with io.BytesIO(screenshot_data) as file:
        try:
            screenshot = Image.open(file)
            screenshot.verify()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to parse screenshot file", exc_info=exc)
            return ServiceError.SCREENSHOTS_IMAGE_INVALID

        screenshot_id = uuid4()
        screenshot_name = secrets.token_urlsafe(16)
        screenshot_size = len(screenshot_data)
        screenshot_type = screenshot.format
        screenshot_download_url = s3.get_s3_public_url(
            "osu-server-professing", f"screenshots/{screenshot_name}"
        )

        assert screenshot_type is not None

    # Upload to Amazon S3
    try:
        await s3.upload(screenshot_data, screenshot_name, "screenshots")
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    # Store screenshot metadata in database
    try:
        screenshot = await screenshots.create(
            screenshot_id=screenshot_id,
            file_name=screenshot_name,
            file_type=screenshot_type,
            file_size=screenshot_size,
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
