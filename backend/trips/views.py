import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .planner import HOSPlanner, parse_departure
from .providers import MapProvider, ProviderError, coordinate_at_progress


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_POST
def plan_trip(request):
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _error("Request body must be valid JSON.")

    required = ["current_location", "pickup_location", "dropoff_location"]
    missing = [field for field in required if not str(body.get(field, "")).strip()]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}.")

    try:
        cycle_used = float(body.get("current_cycle_used", 0))
    except (TypeError, ValueError):
        return _error("Current cycle used must be a number between 0 and 70.")
    if not 0 <= cycle_used <= 70:
        return _error("Current cycle used must be between 0 and 70 hours.")

    try:
        departure = parse_departure(body.get("departure_time"))
    except ValueError:
        return _error("Departure time must be a valid ISO-8601 date and time.")

    provider = MapProvider()
    queries = [body[field].strip() for field in required]
    try:
        locations = provider.geocode_many(queries)
        route = provider.route(locations)
    except ProviderError as exc:
        return _error(str(exc), status=502)

    plan = HOSPlanner(departure, cycle_used).build(route["legs"])
    stops = _build_stops(plan["events"], route)

    return JsonResponse(
        {
            "locations": {
                "current": locations[0],
                "pickup": locations[1],
                "dropoff": locations[2],
            },
            "route": route,
            "schedule": plan["events"],
            "daily_logs": plan["daily_logs"],
            "stops": stops,
            "summary": plan["summary"],
            "compliance": {
                "cycle": "70 hours / 8 days",
                "rules": [
                    "Maximum 11 driving hours after 10 consecutive hours off duty",
                    "No driving beyond the 14th consecutive hour after coming on duty",
                    "30-minute non-driving break after 8 cumulative driving hours",
                    "34 consecutive hours off duty resets the 70-hour cycle",
                    "Fuel stop scheduled at least once every 1,000 miles",
                    "One hour each for pickup and drop-off",
                ],
                "assumption": "The trip starts after a qualifying 10-hour off-duty period. Rolling recap hours cannot be inferred from a single cycle-used total, so a conservative 34-hour restart is scheduled when needed.",
            },
        }
    )


def _build_stops(events, route):
    total = max(route["distance_miles"], 0.1)
    stops = []
    for event in events:
        if event["kind"] not in {"fuel", "break", "daily_rest", "cycle_restart"}:
            continue
        coordinate = coordinate_at_progress(
            route["geometry"], min(1, event["route_progress_miles"] / total)
        )
        if coordinate:
            stops.append(
                {
                    "kind": event["kind"],
                    "title": event["title"],
                    "time": event["start"],
                    "coordinate": coordinate,
                    "mile": event["route_progress_miles"],
                }
            )
    return stops


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)

