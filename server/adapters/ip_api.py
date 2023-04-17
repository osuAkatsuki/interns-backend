from typing import Any

from server import clients


async def fetch_geolocation_from_ip_address(ip_address: str) -> dict[str, Any] | None:
    url = f"http://ip-api.com/json/{ip_address}"
    response = await clients.http_client.get(url)
    if response.status_code not in range(200, 300):
        return None

    return response.json()
