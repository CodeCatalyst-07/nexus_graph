# Deployment Guide & Tips
## NexusGraph Support — Context-Aware Customer Support Agent (PS-1)
### Neo4j × hackFront India Agent Memory Build Sprint Pune

---

### Architecture Overview
1. **Database:** **Already Deployed!** Your Neo4j AuraDB instance is cloud-hosted and accessible over the internet via the encrypted Bolt protocol (`neo4j+s://9560a96b.databases.neo4j.io:7687`). Zero DB deployment needed.
2. **Backend:** FastAPI (Python 3.11). Runs on any container or Python PaaS.
3. **Frontend:** React + Vite SPA. Builds to static files in `dist/` and runs on any CDN.

---

## 🚀 The Fastest Strategy: Vercel + Render / Railway (Takes ~8 Mins)

### Part 1: Deploy the Backend (e.g., [Render.com](https://render.com) or [Railway.app](https://railway.app))

1. Push your repository to GitHub.
2. On Render/Railway, create a new **Web Service** and connect your GitHub repo.
3. Configure the service settings:
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the **Environment Variables**:
   ```ini
   NEO4J_URI=neo4j+s://<your-aura-instance-id>.databases.neo4j.io:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=<your-rotated-neo4j-password>
   NEO4J_DATABASE=neo4j
   GEMINI_API_KEY=<your-gemini-api-key-optional>
   CORS_ORIGINS=*
   ```
5. Click **Deploy**. Note down your live backend URL (e.g. `https://nexusgraph-api.onrender.com`).

---

### Part 2: Deploy the Frontend (e.g., [Vercel](https://vercel.com) or [Netlify](https://netlify.com))

1. On Vercel or Netlify, click **Add New Project** and select your GitHub repo.
2. Configure build settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add the **Environment Variable**:
   ```ini
   VITE_API_BASE_URL=https://nexusgraph-api.onrender.com
   ```
   *(Replace with your actual Render/Railway backend URL from Part 1)*
4. Click **Deploy**. Your interactive UI is now live on `https://your-project.vercel.app`!

---

## 💡 Crucial Pro-Tips & Gotchas

> [!TIP]
> **1. Client Base URL is Already Configured**
> We have already updated [`frontend/src/api/client.js`](file:///Users/arnav/Desktop/neo4j_hackathon/frontend/src/api/client.js#L1) to look for `import.meta.env.VITE_API_BASE_URL`.
> - When running locally: it falls back to `/api` (routed via Vite's proxy).
> - When deployed: it sends API requests directly to your cloud backend URL.

> [!WARNING]
> **2. Prevent Free-Tier Spin-Downs on Demo Day**
> Free instances on Render spin down after 15 minutes of inactivity. When judges click your link, a cold start can take 45–60 seconds.
> - **Solution:** Use a free monitor like [UptimeRobot](https://uptimerobot.com) to ping `https://nexusgraph-api.onrender.com/` every 5 minutes so it stays awake during judging.

> [!IMPORTANT]
> **3. CORS Settings**
> In [`backend/app/config.py`](file:///Users/arnav/Desktop/neo4j_hackathon/backend/app/config.py#L22), `CORS_ORIGINS` defaults to localhost. Setting `CORS_ORIGINS=*` in your cloud provider's environment settings ensures your Vercel frontend won't get blocked by browser CORS restrictions.

> [!NOTE]
> **4. Neo4j Encrypted Protocol**
> Always keep `neo4j+s://` in `NEO4J_URI`. Neo4j AuraDB requires encrypted TLS connections; changing it to `bolt://` or `neo4j://` will cause connection timeouts on cloud hosts.

---

## Alternative: Single Docker Container (GCP Cloud Run / AWS)

If you prefer deploying a single container where the FastAPI server serves both the API and the pre-built React frontend (eliminating CORS entirely):

```dockerfile
# Dockerfile in project root
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-builder /app/frontend/dist ./static

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```
