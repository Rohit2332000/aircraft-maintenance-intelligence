# Aircraft Maintenance Intelligence — Frontend

A production-style React/Vite dashboard wired to the FastAPI endpoint:

`POST /api/v1/aircraft/{aircraft_id}/analysis`

## Run

```bash
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

The frontend defaults to:

`http://localhost:8000`

To change it, create `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Backend

Start FastAPI from your backend directory:

```bash
python app.py
```

The frontend sends:

- URL parameter: `aircraft_id`
- multipart form field: `file`
- file types: `.xlsx`, `.xls`

## What the UI uses from your JSON

Aircraft:
- `aircraft.aircraft_id`
- `risk_score`
- `remaining_useful_life`
- `overall_status`
- `parameters_analyzed`
- `anomalies_detected`
- `maintenance_required_count`

Each parameter:
- `display_name`
- `unit`
- `analytics.latest_value`
- `analytics.historical.mean/median/std`
- `analytics.z_score`
- `analytics.trend`
- `analytics.statistical_anomaly`
- `normal_range`
- `manual_status`
- `manual_evidence_available`
- `maintenance.maintenance_required`
- `maintenance.priority`
- `maintenance.recommended_action`
- `maintenance.reasoning`
- `maintenance.failure_modes`
- `maintenance.confidence`

## Important

The dashboard does not hard-code aircraft values. It renders the JSON returned by your FastAPI pipeline.
