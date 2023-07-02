from app import clients
from app import settings


async def verify_recaptcha(recaptcha_token: str) -> bool:
    response = await clients.http_client.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": recaptcha_token,
            # TODO: Attach "remoteip" field: https://stackoverflow.com/a/51920956
        },
    )
    response.raise_for_status()
    response_data = response.json()
    if not isinstance(response_data, dict):
        raise ValueError("Invalid response from recaptcha")

    return response_data.get("success", False)
