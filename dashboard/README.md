# Market Analytics Health Dashboard (Phase 3)

## Planned Stack

| Layer       | Technology            |
|-------------|-----------------------|
| Framework   | React 18 + TypeScript |
| UI Library  | Tailwind CSS + shadcn |
| Charts      | Recharts              |
| Data        | FastAPI `/health` endpoint polling |

## Planned Panels

1. **Pipeline Latency** -- time from API call to Snowflake commit, displayed as a rolling line chart.
2. **Data Freshness** -- per-symbol staleness gauge (green < 5 min, yellow < 15 min, red > 15 min).
3. **API Success Rate** -- success/failure ring chart over the last 24 hours.
4. **Ingestion Log** -- scrollable table of recent ingestion results from `/ingest` responses.

## Getting Started (future)

```bash
cd dashboard
npx create-next-app@latest . --typescript --tailwind
npm install recharts
npm run dev
```
