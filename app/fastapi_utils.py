from typing import Any

import fastapi.openapi.utils
import starlette.routing
from fastapi import FastAPI as _FastAPI


# XXX: app.host is directly from starlette, and is not fully supported
# by the fastapi wrapper; because of this, these routes will not be shown
# in the automatically generated documentation; this is our fix for that.
# we will probably want to try finding a better solution for this.
class FastAPI(_FastAPI):
    def openapi(self) -> dict[str, Any]:
        if not self.openapi_schema:
            routes = self.routes
            starlette_hosts = [
                host
                for host in super().routes
                if isinstance(host, starlette.routing.Host)
            ]

            for host in starlette_hosts:
                for route in host.routes:
                    if route not in routes:
                        routes.append(route)

            self.openapi_schema = fastapi.openapi.utils.get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )

        return self.openapi_schema
