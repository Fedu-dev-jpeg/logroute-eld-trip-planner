# LogRoute ELD Trip Planner

LogRoute is a full-stack Django and React assessment project. It converts a current location, pickup, drop-off, departure time, and current 70-hour cycle usage into:

- an OpenStreetMap route with pickup, drop-off, fuel, break, and reset markers;
- a conservative FMCSA hours-of-service schedule;
- a chronological driver itinerary; and
- one filled daily log sheet per calendar day, downloadable as PNG.

## Repository structure

```text
spotter-eld-trip-planner/
├── backend/               Django JSON API and HOS scheduling engine
│   ├── config/            Settings and URL configuration
│   ├── trips/             Providers, planning logic, endpoints, and tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              React and Vite single-page application
│   ├── public/            Blank FMCSA log sheet image
│   ├── src/components/    Form, map, timeline, summaries, and ELD sheet
│   ├── Dockerfile
│   └── package.json
├── docs/                  Architecture and Loom walkthrough notes
├── LOOM_GUIDE.txt         Ready-to-read recording script
├── docker-compose.yml
└── render.yaml
```

## Rules implemented

The scheduler models a property-carrying driver under the 70-hour/8-day cycle:

- up to 11 driving hours after 10 consecutive off-duty hours;
- no driving after the 14th consecutive hour after coming on duty;
- a 30-minute non-driving break after 8 cumulative driving hours;
- no driving after 70 on-duty hours in 8 days;
- a 34-hour off-duty restart when the available cycle is exhausted;
- a 30-minute fuel and safety stop every 900 miles, keeping the plan below the required 1,000-mile interval; and
- one on-duty hour at pickup and one at drop-off.

The input supplies only a single `current_cycle_used` total, not the preceding eight daily records. Therefore, rolling recap hours cannot be inferred. The planner deliberately uses a 34-hour restart when the remaining cycle is exhausted. It also assumes the trip begins after a qualifying 10-hour off-duty period and does not use adverse-driving or sleeper-berth exceptions.

This is a planning demonstration, not a certified ELD or legal advice.

## Local setup

### Option A: Docker

```bash
docker compose up --build
```

Open `http://localhost:5173`. The API health check is at `http://localhost:8000/api/health/`.

### Option B: run each app

Backend (Python 3.10+):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend (Node 20.19+ or 22.12+):

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The Vite development server proxies `/api` to Django, so `VITE_API_URL` is optional locally.

## Tests and quality checks

```bash
cd backend
python manage.py test

cd ../frontend
npm run lint
npm run build
```

Backend tests cover long-trip breaks and resets, 34-hour restarts near the cycle limit, 24-hour daily-log totals, validation, and the API response contract.

## API

`POST /api/plan/`

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Indianapolis, IN",
  "dropoff_location": "Atlanta, GA",
  "current_cycle_used": 18.5,
  "departure_time": "2026-10-01T08:00:00-05:00"
}
```

The response includes geocoded locations, GeoJSON route geometry, route legs and directions, the HOS event schedule, map stops, daily logs, trip totals, and compliance notes.

## Map services

The backend uses Nominatim for geocoding and OSRM for routing. Geocoding is cached for 24 hours, requests are serialized to respect the public Nominatim limit, and the application sends an identifying user agent. Before public deployment, set `MAP_USER_AGENT` to a value that includes a real contact address. For production or material traffic, use a hosted/self-hosted provider rather than the public demo services.

## Deployment

### Render blueprint

`render.yaml` creates a Django web service and a static React site. After the backend deploys:

1. set the frontend `VITE_API_URL` to `https://YOUR-BACKEND.onrender.com/api`;
2. set backend `CORS_ALLOWED_ORIGINS` to the frontend origin;
3. set a strong `DJANGO_SECRET_KEY`; and
4. set `MAP_USER_AGENT` with a contact email.

### Vercel frontend and Render backend

Import the repository twice:

- Vercel: set the root directory to `frontend` and `VITE_API_URL` to the Render API URL.
- Render: create a Python web service with root directory `backend`, build command `pip install -r requirements.txt && python manage.py collectstatic --noinput`, and start command `gunicorn config.wsgi:application`.

### Vercel frontend and backend

Vercel supports Django through its Python runtime. Import this repository twice:

- API project: root directory `backend`, with `DJANGO_ALLOWED_HOSTS=.vercel.app`, `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY`, and `CORS_ALLOWED_ORIGINS` set to the frontend origin.
- Web project: root directory `frontend`, with `VITE_API_URL` set to the API deployment URL followed by `/api`.

## Sources

- [FMCSA Summary of Hours of Service Regulations](https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations)
- [FMCSA Interstate Truck Driver's Guide to Hours of Service](https://www.fmcsa.dot.gov/regulations/hours-service/interstate-truck-drivers-guide-hours-service)
- [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)
- [OSRM API Documentation](https://project-osrm.org/docs/)
