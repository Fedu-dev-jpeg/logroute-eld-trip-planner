import json
from unittest.mock import patch

from django.test import SimpleTestCase


class PlanTripViewTests(SimpleTestCase):
    @patch("trips.views.MapProvider")
    def test_plan_endpoint_returns_route_and_logs(self, provider_class):
        provider = provider_class.return_value
        provider.geocode_many.return_value = [
            {"label": "A", "lat": 1, "lon": 1},
            {"label": "B", "lat": 2, "lon": 2},
            {"label": "C", "lat": 3, "lon": 3},
        ]
        provider.route.return_value = {
            "distance_miles": 600,
            "duration_hours": 10,
            "geometry": {"type": "LineString", "coordinates": [[1, 1], [2, 2], [3, 3]]},
            "legs": [
                {"name": "Current location to pickup", "distance_miles": 100, "duration_hours": 2, "steps": []},
                {"name": "Pickup to drop-off", "distance_miles": 500, "duration_hours": 8, "steps": []},
            ],
        }
        response = self.client.post(
            "/api/plan/",
            data=json.dumps(
                {
                    "current_location": "A",
                    "pickup_location": "B",
                    "dropoff_location": "C",
                    "current_cycle_used": 12,
                    "departure_time": "2026-10-01T08:00:00Z",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["route"]["distance_miles"], 600)
        self.assertGreaterEqual(len(payload["daily_logs"]), 1)

    def test_invalid_cycle_is_rejected(self):
        response = self.client.post(
            "/api/plan/",
            data=json.dumps(
                {
                    "current_location": "A",
                    "pickup_location": "B",
                    "dropoff_location": "C",
                    "current_cycle_used": 71,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

