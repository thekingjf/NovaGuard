# NovaGuard Backend Deployment

This backend is a Flask API that should be run with a production WSGI server (gunicorn) and can be deployed to several platforms.

## 1) Render (recommended)
- Create a new Web Service pointing to this repo/folder
- Root Directory: `backend/`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT api_server:app`
- Environment:
  - `CORS_ORIGINS`: `https://<your-frontend-domain>` (comma-separated if multiple)
  - `PYTHONUNBUFFERED=1`

## 2) Railway
- Create a new service from repo
- Service root: `backend/`
- Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT api_server:app`

## 3) Google Cloud Run
- Build with Dockerfile in `backend/`
- Expose port 5001 (or Cloud Run will inject $PORT)
- Set `CORS_ORIGINS` to your frontend domain

## 4) Vercel note
Vercel Serverless Functions for Python are limited and not ideal for OpenCV + long running video processing. Instead, deploy the Flask server to a separate service (Render/Railway/Cloud Run) and point your frontend to it via environment variables and rewrites.

## Health
- GET `/api/health` returns `{ status: 'healthy' }`.
