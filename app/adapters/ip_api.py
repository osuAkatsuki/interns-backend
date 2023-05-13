from typing import Any

from httpx import HTTPError

from app import clients


async def fetch_geolocation_from_ip_address(ip_address: str) -> dict[str, Any] | None:
    url = f"http://ip-api.com/json/{ip_address}"
    try:
        response = await clients.http_client.get(url)
        response.raise_for_status()
    except HTTPError:
        return None
    else:
        return response.json()
