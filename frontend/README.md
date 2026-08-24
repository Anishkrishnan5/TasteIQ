# TasteIQ frontend

This directory contains the React and Vite interface for TasteIQ. It submits meal queries and
optional nutrition constraints to the FastAPI service, then renders grounded menu results.

## Development

```bash
npm install
npm run dev
```

The development server proxies `/api` and `/health` to `http://127.0.0.1:8000`; start the backend as
described in the repository README. Set `VITE_API_URL` only when the API uses a different origin.

## Checks

```bash
npm run lint
npm run build
npm run test:e2e
```

The Playwright test starts both applications and exercises a real recommendation request. Production
builds are served by unprivileged Nginx, which forwards same-origin API requests to the backend.
