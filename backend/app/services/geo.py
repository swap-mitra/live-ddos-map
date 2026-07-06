from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeoResult:
    lat: float
    lng: float
    country: str | None
    country_code: str | None
    asn: str | None = None


def _parse_response(response) -> GeoResult | None:
    """Extract lat/lng/country from a geoip2 city response object."""
    location = response.location
    if location.latitude is None or location.longitude is None:
        return None

    return GeoResult(
        lat=float(location.latitude),
        lng=float(location.longitude),
        country=response.country.name,
        country_code=response.country.iso_code,
        asn=None,
    )


def _is_global_ip(ip: str) -> bool:
    """Return True if the IP is a publicly routable address."""
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return parsed.is_global


class GeoLocator:
    """MaxMind-backed IP geolocation.

    Supports two modes:
      1. **Web service** (recommended) — uses geoip2.webservice.AsyncClient
         with the free GeoLite2 endpoint (geolite.info). No .mmdb file needed.
         Requires MAXMIND_ACCOUNT_ID + MAXMIND_LICENSE_KEY.
      2. **Local database** — uses geoip2.database.Reader with a .mmdb file.
         Requires MAXMIND_DB_PATH pointing to GeoLite2-City.mmdb.

    Web service mode is tried first. If credentials are absent, falls back
    to the local database. If neither is configured, geolocation is disabled.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        *,
        account_id: int | None = None,
        license_key: str | None = None,
    ) -> None:
        self._reader = None
        self._web_client = None
        self._mode = "disabled"

        # Prefer web service mode (no file management needed)
        if account_id and license_key:
            import geoip2.webservice

            self._web_client = geoip2.webservice.AsyncClient(
                account_id,
                license_key,
                host="geolite.info",  # Free GeoLite2 web service
            )
            self._mode = "webservice"
            logger.info("GeoLocator using GeoLite2 web service (geolite.info)")
            return

        # Fallback to local .mmdb database
        if db_path and db_path.exists():
            import geoip2.database

            self._reader = geoip2.database.Reader(str(db_path))
            self._mode = "database"
            logger.info("GeoLocator using local database: %s", db_path)
            return

        if db_path and not db_path.exists():
            logger.warning("MaxMind database not found at %s", db_path)

        logger.warning(
            "IP geolocation is disabled. Set MAXMIND_ACCOUNT_ID + MAXMIND_LICENSE_KEY "
            "for web service mode, or MAXMIND_DB_PATH for local database mode."
        )

    @property
    def mode(self) -> str:
        return self._mode

    async def lookup_ip(self, ip: str | None) -> GeoResult | None:
        if not ip or self._mode == "disabled":
            return None

        if not _is_global_ip(ip):
            return None

        try:
            if self._web_client:
                response = await self._web_client.city(ip)
            elif self._reader:
                response = self._reader.city(ip)
            else:
                return None
        except Exception as exc:
            logger.debug("Geo lookup failed for %s: %s", ip, exc)
            return None

        return _parse_response(response)

    async def close(self) -> None:
        if self._web_client:
            await self._web_client.close()
        if self._reader:
            self._reader.close()
