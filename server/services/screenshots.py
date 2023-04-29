from typing import Any
from uuid import UUID, uuid4
from server.errors import ServiceError
from PIL import Image
import io
from server import logger
from server.adapters import s3

import secrets
import server.repositories.screenshots as screenshots


async def create(
    screenshot_data: bytes,
) -> dict[str, Any] | ServiceError:
    with io.BytesIO(screenshot_data) as file:
        try:
            screenshot = Image.open(file)
            screenshot.verify()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to parse screenshot file", exc_info=exc)
            return ServiceError.SCREENSHOTS_IMAGE_INVALID

        screenshot_name = secrets.token_urlsafe(16)
        screenshot_size = len(screenshot_data)
        screenshot_filetype = screenshot.format
        screenshot_id = uuid4()


    # TODO: upload image to AWS S3
    try:
        ...
    except Exception as exc:# pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    # TODO: save screenshot metadata to database
    try:
        screenshot = await screenshots.create(
            screenshot_id=,
            file_name=,
            file_type=,
            file_size=file_size,
            download_url=, # determine where it was uploaded on s3 (a publicly accessible url to the image)
        )
    except Exception as exc: # pragma: no cover
        logger.error("Failed to upload screenshot file", exc_info=exc)
        return ServiceError.SCREENSHOTS_UPLOAD_FAILED

    return screenshot
