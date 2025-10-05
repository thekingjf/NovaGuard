## 1) Render 
- Create a new Web Service pointing to this repo/folder
- Root Directory: `backend/`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT api_server:app`
- Environment:
  - `CORS_ORIGINS`: `https://<your-frontend-domain>` (comma-separated if multiple, NO trailing slash)
  - `PYTHONUNBUFFERED=1`

### Frontend wiring (Vercel)
- In Vercel Project → Settings → Environment Variables:
  - Set `VITE_API_BASE` to your backend base URL including `/api` (e.g., `https://<render-service>.onrender.com/api`).
  - Redeploy the frontend
