from datetime import datetime, timezone

from django.test import SimpleTestCase

from trips.planner import HOSPlanner


class HOSPlannerTests(SimpleTestCase):
    def make_plan(self, hours, miles, cycle=0):
        return HOSPlanner(
            datetime(2026, 10, 1, 8, tzinfo=timezone.utc), cycle
        ).build(
            [
                {"name": "Current location to pickup", "duration_hours": hours / 2, "distance_miles": miles / 2},
                {"name": "Pickup to drop-off", "duration_hours": hours / 2, "distance_miles": miles / 2},
            ]
        )

    def test_long_trip_adds_break_and_daily_reset(self):
        plan = self.make_plan(18, 1080)
        kinds = [event["kind"] for event in plan["events"]]
        self.assertIn("break", kinds)
        self.assertIn("daily_rest", kinds)
        self.assertIn("fuel", kinds)

    def test_near_cycle_limit_adds_34_hour_restart(self):
        plan = self.make_plan(8, 480, cycle=68)
        self.assertIn("cycle_restart", [event["kind"] for event in plan["events"]])

    def test_one_hour_pickup_resets_eight_hour_break_clock(self):
        plan = HOSPlanner(
            datetime(2026, 10, 1, 8, tzinfo=timezone.utc), 0
        ).build(
            [
                {"name": "Current location to pickup", "duration_hours": 3.5, "distance_miles": 210},
                {"name": "Pickup to drop-off", "duration_hours": 5, "distance_miles": 300},
            ]
        )
        self.assertNotIn("break", [event["kind"] for event in plan["events"]])

    def test_each_daily_log_totals_24_hours(self):
        plan = self.make_plan(25, 1500)
        for log in plan["daily_logs"]:
            self.assertAlmostEqual(sum(log["totals"].values()), 24, places=2)

    def test_driving_blocks_do_not_exceed_limits(self):
        plan = self.make_plan(30, 1800)
        since_break = 0
        shift_drive = 0
        for event in plan["events"]:
            if event["kind"] in {"daily_rest", "cycle_restart"}:
                since_break = 0
                shift_drive = 0
            elif event["kind"] in {"break", "fuel"}:
                since_break = 0
            elif event["status"] == "driving":
                since_break += event["duration_hours"]
                shift_drive += event["duration_hours"]
                self.assertLessEqual(since_break, 8.001)
                self.assertLessEqual(shift_drive, 11.001)
