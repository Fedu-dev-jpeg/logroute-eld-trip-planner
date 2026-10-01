from collections import defaultdict
from datetime import datetime, time, timedelta, timezone


EPSILON = 1e-6


class HOSPlanner:
    """Conservative property-carrying schedule under the 70-hour/8-day rule."""

    def __init__(self, departure_time, current_cycle_used):
        self.now = departure_time
        self.cycle_used = float(current_cycle_used)
        self.shift_elapsed = 0.0
        self.shift_driving = 0.0
        self.driving_since_break = 0.0
        self.progress_miles = 0.0
        self.next_fuel_mile = 900.0
        self.events = []

    def build(self, legs):
        for index, leg in enumerate(legs):
            self._drive_leg(leg)
            if index == 0:
                self._add_service("pickup", "Pickup and cargo securement", 1.0)
        self._add_service("dropoff", "Drop-off and paperwork", 1.0)

        return {
            "events": self.events,
            "daily_logs": build_daily_logs(self.events),
            "summary": self._summary(),
        }

    def _drive_leg(self, leg):
        remaining_miles = float(leg["distance_miles"])
        remaining_hours = max(float(leg["duration_hours"]), EPSILON)
        leg_name = leg["name"]

        while remaining_hours > EPSILON:
            if self.cycle_used >= 70 - EPSILON:
                self._add_reset(34, "cycle_restart", "34-hour cycle restart")
                continue
            if self.shift_driving >= 11 - EPSILON or self.shift_elapsed >= 14 - EPSILON:
                self._add_reset(10, "daily_rest", "10-hour off-duty reset")
                continue
            if self.driving_since_break >= 8 - EPSILON:
                self._add_break()
                continue

            speed = remaining_miles / remaining_hours
            hours_to_fuel = float("inf")
            if self.progress_miles + remaining_miles >= self.next_fuel_mile - EPSILON:
                hours_to_fuel = max(
                    0.0, (self.next_fuel_mile - self.progress_miles) / speed
                )

            chunk = min(
                remaining_hours,
                11 - self.shift_driving,
                14 - self.shift_elapsed,
                8 - self.driving_since_break,
                70 - self.cycle_used,
                hours_to_fuel,
            )

            if chunk <= EPSILON:
                if hours_to_fuel <= EPSILON:
                    self._add_fuel_stop()
                elif 70 - self.cycle_used <= EPSILON:
                    self._add_reset(34, "cycle_restart", "34-hour cycle restart")
                elif 8 - self.driving_since_break <= EPSILON:
                    self._add_break()
                else:
                    self._add_reset(10, "daily_rest", "10-hour off-duty reset")
                continue

            miles = min(remaining_miles, speed * chunk)
            self._append(
                status="driving",
                kind="driving",
                title=f"Drive: {leg_name}",
                duration=chunk,
                miles=miles,
            )
            self.shift_elapsed += chunk
            self.shift_driving += chunk
            self.driving_since_break += chunk
            self.cycle_used += chunk
            self.progress_miles += miles
            remaining_hours -= chunk
            remaining_miles -= miles

            if (
                self.progress_miles >= self.next_fuel_mile - 0.01
                and remaining_hours > EPSILON
            ):
                self._add_fuel_stop()

    def _add_service(self, kind, title, duration):
        if self.cycle_used + duration > 70 + EPSILON:
            self._add_reset(34, "cycle_restart", "34-hour cycle restart")
        self._append("on_duty", kind, title, duration)
        self.shift_elapsed += duration
        self.cycle_used += duration
        if duration >= 0.5:
            self.driving_since_break = 0.0

    def _add_break(self):
        self._append(
            "off_duty",
            "break",
            "30-minute DOT break",
            0.5,
        )
        self.shift_elapsed += 0.5
        self.driving_since_break = 0.0

    def _add_fuel_stop(self):
        if self.cycle_used + 0.5 > 70 + EPSILON:
            self._add_reset(34, "cycle_restart", "34-hour cycle restart")
        self._append(
            "on_duty",
            "fuel",
            "Fuel and vehicle check",
            0.5,
        )
        self.shift_elapsed += 0.5
        self.cycle_used += 0.5
        self.driving_since_break = 0.0
        self.next_fuel_mile += 900.0

    def _add_reset(self, hours, kind, title):
        self._append("off_duty", kind, title, hours)
        self.shift_elapsed = 0.0
        self.shift_driving = 0.0
        self.driving_since_break = 0.0
        if hours >= 34:
            self.cycle_used = 0.0

    def _append(self, status, kind, title, duration, miles=0.0):
        start = self.now
        end = start + timedelta(hours=duration)
        self.events.append(
            {
                "status": status,
                "kind": kind,
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration_hours": round(duration, 2),
                "miles": round(miles, 1),
                "route_progress_miles": round(self.progress_miles + miles, 1),
            }
        )
        self.now = end

    def _summary(self):
        driving = sum(e["duration_hours"] for e in self.events if e["status"] == "driving")
        on_duty = sum(
            e["duration_hours"]
            for e in self.events
            if e["status"] in {"driving", "on_duty"}
        )
        return {
            "trip_duration_hours": round(
                (datetime.fromisoformat(self.events[-1]["end"]) - datetime.fromisoformat(self.events[0]["start"])).total_seconds()
                / 3600,
                1,
            ),
            "driving_hours": round(driving, 1),
            "on_duty_hours": round(on_duty, 1),
            "ending_cycle_used_hours": round(self.cycle_used, 1),
            "fuel_stops": sum(e["kind"] == "fuel" for e in self.events),
            "daily_resets": sum(e["kind"] == "daily_rest" for e in self.events),
            "cycle_restarts": sum(e["kind"] == "cycle_restart" for e in self.events),
        }


def parse_departure(value):
    if not value:
        return datetime.now(timezone.utc).replace(second=0, microsecond=0)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_daily_logs(events):
    if not events:
        return []
    parsed = [
        {**event, "start_dt": datetime.fromisoformat(event["start"]), "end_dt": datetime.fromisoformat(event["end"])}
        for event in events
    ]
    first = parsed[0]["start_dt"]
    last = parsed[-1]["end_dt"]
    current_date = first.date()
    final_date = last.date()
    logs = []

    while current_date <= final_date:
        day_start = datetime.combine(current_date, time.min, tzinfo=first.tzinfo)
        day_end = day_start + timedelta(days=1)
        slices = []
        cursor = day_start

        for event in parsed:
            start = max(event["start_dt"], day_start)
            end = min(event["end_dt"], day_end)
            if start >= end:
                continue
            if cursor < start:
                slices.append(_day_slice("off_duty", "Off duty", cursor, start, day_start))
            slices.append(
                _day_slice(
                    event["status"],
                    event["title"],
                    start,
                    end,
                    day_start,
                    event["kind"],
                )
            )
            cursor = max(cursor, end)

        if cursor < day_end:
            slices.append(_day_slice("off_duty", "Off duty", cursor, day_end, day_start))

        totals = defaultdict(float)
        for item in slices:
            totals[item["status"]] += item["duration_hours"]
        logs.append(
            {
                "date": current_date.isoformat(),
                "events": slices,
                "totals": {
                    status: round(totals[status], 2)
                    for status in ["off_duty", "sleeper_berth", "driving", "on_duty"]
                },
            }
        )
        current_date += timedelta(days=1)
    return logs


def _day_slice(status, title, start, end, day_start, kind="off_duty"):
    return {
        "status": status,
        "kind": kind,
        "title": title,
        "start_hour": round((start - day_start).total_seconds() / 3600, 4),
        "end_hour": round((end - day_start).total_seconds() / 3600, 4),
        "duration_hours": round((end - start).total_seconds() / 3600, 4),
    }
