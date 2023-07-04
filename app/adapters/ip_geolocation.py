from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from app import clients
from app import logger


@dataclass
class Geolocation:
    # {"status":"success","countryCode":"US","region":"VA","lat":39.0438,"lon":-77.4874}
    status: str
    message: str
    country_code: str
    region: str
    lat: float
    lon: float


def deserialize(data: Mapping[str, Any]) -> Geolocation:
    return Geolocation(
        status=data["status"],
        message=data["message"],
        country_code=data["countryCode"],
        region=data["region"],
        lat=data["lat"],
        lon=data["lon"],
    )


async def get_geolocation(ip_address: str) -> Geolocation:
    """\
    Resolve geolocation data from a given IP address using ip-api.com.

    Documentation: https://ip-api.com/docs/api:json
    """
    try:
        response = await clients.http_client.get(
            url=f"http://ip-api.com/json/{ip_address}",
            params={"fields": "status,message,countryCode,region,lat,lon"},
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch geolocation from ip-api",
            exc_info=exc,
            ip_address=ip_address,
        )
        raise  # TODO: handle this with retry logic

    response_data = response.json()
    return deserialize(response_data)
