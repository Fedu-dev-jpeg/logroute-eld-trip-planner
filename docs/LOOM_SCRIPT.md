# Suggested 3 to 5 minute Loom walkthrough

## 0:00 to 0:35 Product overview

Show the landing page and explain that LogRoute turns dispatch inputs into a route a property-carrying driver can legally complete, plus daily log sheets.

## 0:35 to 1:25 End-to-end demo

Use the prefilled Chicago to Indianapolis to Atlanta example. Point out the distance, total elapsed time, driving time, and number of logs. On the map, show the three route locations and compliance-stop markers.

## 1:25 to 2:05 HOS schedule

Scroll through the driver timeline. Explain pickup/drop-off service, the 30-minute break after eight cumulative driving hours, the 11-hour limit, the 14-hour window, ten-hour daily rest, fuel before 1,000 miles, and the 70-hour cycle.

## 2:05 to 2:45 Daily logs

Switch between day tabs, point out that every sheet totals 24 hours, and download one PNG. Mention that the graph is rendered on the supplied blank log sheet.

## 2:45 to 3:45 Code tour

Open `backend/trips/planner.py` for the pure scheduling engine, `providers.py` for cached Nominatim/OSRM access, and the backend tests. Then show `frontend/src/App.jsx`, `RouteMap.jsx`, and `LogSheet.jsx`.

## 3:45 to 4:20 Tradeoffs and next steps

Explain the conservative 34-hour restart: a single current-cycle total is not enough to calculate rolling recap. Mention that production should use truck-aware routing, actual truck-stop availability, time-zone handling, persistence, authentication, and certified ELD integration.

