import math
import os
import time
from hashlib import sha256

import requests
from django.core.cache import cache


MILES_PER_METER = 0.000621371


class ProviderError(RuntimeError):
    pass


class MapProvider:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.nominatim_url = os.getenv(
            "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
        ).rstrip("/")
        self.osrm_url = os.getenv(
            "OSRM_BASE_URL", "https://router.project-osrm.org"
        ).rstrip("/")
        self.headers = {
            "User-Agent": os.getenv(
                "MAP_USER_AGENT", "SpotterELDPlanner/1.0 (assessment-demo)"
            )
        }

    def geocode(self, query):
        digest = sha256(query.strip().lower().encode("utf-8")).hexdigest()
        cache_key = f"geocode:{digest}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = self.session.get(
                f"{self.nominatim_url}/search",
                params={"q": query, "format": "jsonv2", "limit": 1},
                headers=self.headers,
                timeout=12,
            )
            response.raise_for_status()
            results = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError(f"Could not geocode '{query}'.") from exc

        if not results:
            raise ProviderError(f"No location found for '{query}'.")

        result = {
            "label": results[0]["display_name"],
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"]),
        }
        cache.set(cache_key, result, 60 * 60 * 24)
        return result

    def geocode_many(self, queries):
        results = []
        for index, query in enumerate(queries):
            results.append(self.geocode(query))
            if index < len(queries) - 1:
                time.sleep(1.05)
        return results

    def route(self, locations):
        coordinates = ";".join(
            f"{location['lon']},{location['lat']}" for location in locations
        )
        try:
            response = self.session.get(
                f"{self.osrm_url}/route/v1/driving/{coordinates}",
                params={
                    "overview": "simplified",
                    "geometries": "geojson",
                    "steps": "true",
                    "annotations": "false",
                },
                headers=self.headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError("The routing service is temporarily unavailable.") from exc

        if payload.get("code") != "Ok" or not payload.get("routes"):
            raise ProviderError("No drivable route was found for these locations.")

        route = payload["routes"][0]
        legs = []
        for index, leg in enumerate(route["legs"]):
            legs.append(
                {
                    "name": (
                        "Current location to pickup"
                        if index == 0
                        else "Pickup to drop-off"
                    ),
                    "distance_miles": round(leg["distance"] * MILES_PER_METER, 1),
                    "duration_hours": leg["duration"] / 3600,
                    "steps": [self._format_step(step) for step in leg.get("steps", [])],
                }
            )

        return {
            "distance_miles": round(route["distance"] * MILES_PER_METER, 1),
            "duration_hours": route["duration"] / 3600,
            "geometry": route["geometry"],
            "legs": legs,
        }

    @staticmethod
    def _format_step(step):
        maneuver = step.get("maneuver", {})
        kind = maneuver.get("type", "continue").replace("_", " ").title()
        modifier = maneuver.get("modifier", "").replace("_", " ")
        road = step.get("name") or "unnamed road"
        instruction = f"{kind}{f' {modifier}' if modifier else ''} on {road}"
        return {
            "instruction": instruction,
            "distance_miles": round(step.get("distance", 0) * MILES_PER_METER, 1),
            "duration_minutes": round(step.get("duration", 0) / 60),
        }


def coordinate_at_progress(geometry, progress):
    coordinates = geometry.get("coordinates", [])
    if not coordinates:
        return None
    if progress <= 0:
        return coordinates[0]
    if progress >= 1:
        return coordinates[-1]

    distances = []
    total = 0.0
    for start, end in zip(coordinates, coordinates[1:]):
        segment = _haversine_miles(start, end)
        distances.append(segment)
        total += segment
    target = total * progress
    covered = 0.0
    for index, segment in enumerate(distances):
        if covered + segment >= target:
            ratio = 0 if segment == 0 else (target - covered) / segment
            start = coordinates[index]
            end = coordinates[index + 1]
            return [
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            ]
        covered += segment
    return coordinates[-1]


def _haversine_miles(first, second):
    lon1, lat1 = map(math.radians, first)
    lon2, lat2 = map(math.radians, second)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(value))
