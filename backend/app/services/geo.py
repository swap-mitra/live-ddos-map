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


class GeoLocator:
    """MaxMind-backed IP geolocation with a safe no-database mode."""

    def __init__(self, db_path: Path | None) -> None:
        self._reader = None
        if not db_path:
            logger.warning("MAXMIND_DB_PATH is not set; IP geolocation is disabled")
            return
        if not db_path.exists():
            logger.warning("MaxMind database not found at %s; IP geolocation is disabled", db_path)
            return

        import geoip2.database

        self._reader = geoip2.database.Reader(str(db_path))
        logger.info("Loaded MaxMind database from %s", db_path)

    def lookup_ip(self, ip: str | None) -> GeoResult | None:
        if not ip or not self._reader:
            return None

        try:
            parsed = ipaddress.ip_address(ip)
        except ValueError:
            return None

        # Private and reserved addresses should never become public attack arcs.
        if not parsed.is_global:
            return None

        try:
            response = self._reader.city(ip)
        except Exception as exc:  # geoip2 raises several lookup-specific errors.
            logger.debug("Geo lookup failed for %s: %s", ip, exc)
            return None

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

    def close(self) -> None:
        if self._reader:
            self._reader.close()

