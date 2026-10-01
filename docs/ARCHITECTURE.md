# Architecture and planning decisions

## Request flow

1. React validates and submits the five trip inputs to `POST /api/plan/`.
2. Django geocodes the three addresses through Nominatim, with a 24-hour cache and one-request-per-second pacing.
3. Django requests a three-waypoint driving route and turn instructions from OSRM.
4. The HOS engine walks through both route legs, splitting driving around cycle, shift, break, fuel, pickup, and drop-off constraints.
5. Schedule events are split at midnight into complete 24-hour daily logs.
6. The response annotates route progress with approximate coordinates for compliance-stop markers.
7. React renders the route, schedule, compliance summary, and a filled log sheet over the supplied blank log asset.

## Why the HOS engine lives in Django

Keeping regulatory calculations on the server creates one testable source of truth, prevents UI state from changing compliance results, and makes it straightforward to replace the React client or add persistence later.

## Route-progress stop placement

Public OSRM returns route geometry but does not select truck stops. The assessment only requires information regarding stops and rests, so the engine schedules the correct mileage/time and interpolates a marker along the route. A production version should query a commercial truck-stop/parking data source and reroute through a safe facility.

## Important assumptions

- The driver starts with a fresh 11/14-hour clock after 10 hours off duty.
- `current_cycle_used` is the total on-duty time currently charged to the 70-hour cycle.
- Because the previous eight daily records are not inputs, the planner cannot calculate recap hours dropping off the rolling window.
- Fueling takes 30 minutes on duty and satisfies the 30-minute non-driving interruption.
- Pickup and drop-off each take one hour on duty.
- OSRM car-profile duration is an estimate; production truck routing needs vehicle restrictions, governed speed, weather, traffic, and facility access.
- Time-zone changes along a route are not modeled. The departure offset is retained across generated logs.

## Extension points

- Replace `MapProvider` with a commercial truck-routing provider.
- Persist trips and logs in PostgreSQL.
- Add authentication and carrier/driver profiles.
- Collect eight prior daily duty totals to support rolling recap instead of a conservative 34-hour restart.
- Add PDF export and signed ELD records.

