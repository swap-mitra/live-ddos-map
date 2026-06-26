# Deployment Guide

This guide covers deploying the Live DDoS Map to production using Railway (backend) and Vercel (frontend).

## Prerequisites

Before deployment, ensure you have:

- [ ] GitHub repository with the code
- [ ] Railway account (free tier available)
- [ ] Vercel account (free tier available)
- [ ] MaxMind GeoLite2 database downloaded
- [ ] AbuseIPDB API key (free tier)
- [ ] GreyNoise API key (free tier)

## Backend Deployment to Railway

### Step 1: Create Railway Project

1. Log in to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `live-ddos-map` repository
4. Choose the `backend` directory as the root

### Step 2: Configure Build Settings

Railway should auto-detect Python. If not, configure:

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Root Directory:**
```
backend
```

### Step 3: Add Persistent Volume

1. Go to your Railway project → "Volumes" tab
2. Click "New Volume"
3. Configure:
   - **Name**: `ddos-data`
   - **Mount Path**: `/data`
   - **Size**: 1GB (sufficient for 24-hour rolling window)
4. Attach to your backend service

### Step 4: Upload MaxMind Database to Volume

**Option A: Using Railway CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Copy MaxMind database to volume
railway run bash
# Inside the container:
mkdir -p /data
# Exit and use SCP or another method to upload GeoLite2-City.mmdb to /data/
```

**Option B: Using Dockerfile temporary upload**

Create a temporary Dockerfile to upload the database:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY GeoLite2-City.mmdb /data/GeoLite2-City.mmdb
```

Build and deploy once to upload, then remove.

**Option C: Manual via Railway Dashboard**

Some Railway plans allow direct file upload to volumes via the dashboard.

### Step 5: Configure Environment Variables

In Railway dashboard → Variables tab, add:

```bash
DDOS_DB_PATH=/data/events.db
MAXMIND_DB_PATH=/data/GeoLite2-City.mmdb
ABUSEIPDB_KEY=your_production_abuseipdb_key
GREYNOISE_KEY=your_production_greynoise_key
WS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
POLL_INTERVAL_SECONDS=60
EVENT_TTL_HOURS=24
MIN_EVENT_SCORE=0.5
MODEL_PATH=backend/app/ml/model.joblib
ENABLE_HEURISTIC_SCORER=false
ENABLE_SCHEDULER=true
SOURCE_TIMEOUT_SECONDS=10
ABUSEIPDB_BLACKLIST_LIMIT=50
GREYNOISE_LOOKUP_LIMIT=25
TARGET_LAT=37.7749
TARGET_LNG=-122.4194
LOG_LEVEL=INFO
```

**Important**: Update `WS_ALLOWED_ORIGINS` with your actual Vercel deployment URL once you have it.

### Step 6: Deploy

1. Railway will automatically deploy on push to main branch
2. Wait for build to complete
3. Note the generated Railway URL (e.g., `https://your-backend.railway.app`)

### Step 7: Verify Backend

Test health endpoint:

```bash
curl https://your-backend.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "live-ddos-map-backend"
}
```

Test snapshot endpoint:
```bash
curl https://your-backend.railway.app/api/snapshot
```

## Frontend Deployment to Vercel

### Step 1: Create Vercel Project

1. Log in to [Vercel](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure project settings

### Step 2: Configure Build Settings

**Root Directory:**
```
frontend
```

**Framework Preset:**
```
Next.js
```

**Build Command:**
```bash
npm run build
```

**Output Directory:**
```
.next
```

### Step 3: Configure Environment Variables

In Vercel dashboard → Settings → Environment Variables, add:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/ws/attacks
```

**Important**: 
- Use `https://` for API_URL (not `http://`)
- Use `wss://` for WS_URL (not `ws://`)
- Replace `your-backend.railway.app` with your actual Railway URL

### Step 4: Deploy

1. Click "Deploy"
2. Vercel will build and deploy automatically
3. Note the generated Vercel URL (e.g., `https://your-frontend.vercel.app`)

### Step 5: Update Backend CORS Settings

Go back to Railway → Environment Variables and update:

```bash
WS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

**Important**: Remove the `http://localhost:3000` origin in production if you want to restrict access.

### Step 6: Trigger Redeployment

After updating `WS_ALLOWED_ORIGINS`, redeploy the backend:
- In Railway dashboard, click "Redeploy"

### Step 7: Verify Frontend

1. Open your Vercel URL in a browser
2. Check that the globe renders
3. Verify connection status shows "Connected" (green indicator)
4. Wait for events to appear on the dashboard

## Testing the Full Stack

### Test WebSocket Connection

Open browser DevTools → Console and run:

```javascript
const ws = new WebSocket('wss://your-backend.railway.app/ws/attacks');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
```

Expected output:
```
Connected
Message: { kind: "snapshot", events: [...] }
```

### Test REST API

```bash
curl https://your-backend.railway.app/api/snapshot?limit=10
```

Should return JSON with recent events.

### Monitor Backend Logs

In Railway dashboard → Deployments → View Logs:

Look for:
- `Application startup complete`
- `APScheduler started`
- `Poll cycle started`
- `Inserted X new events`
- `Broadcast X events to Y connections`

## Continuous Deployment

### GitHub Actions Setup

The `.github/workflows/ci.yml` file is already configured to:
- Run backend tests on every push
- Build frontend on every push
- Verify code quality

Both Railway and Vercel will auto-deploy on push to main branch if CI passes.

### Manual Deployment

**Railway:**
- Push to main branch triggers automatic deployment
- Or manually redeploy from Railway dashboard

**Vercel:**
- Push to main branch triggers automatic deployment
- Or manually redeploy from Vercel dashboard

## Troubleshooting

### Backend Issues

**"Database locked" errors in Railway logs:**
- SQLite has limited concurrent write support
- Ensure only one backend instance is running
- Check `POLL_INTERVAL_SECONDS` isn't too aggressive

**"MaxMind database not found":**
- Verify volume is mounted at `/data`
- Check `MAXMIND_DB_PATH=/data/GeoLite2-City.mmdb`
- Confirm file exists in volume with `railway run ls -la /data`

**"No events appearing":**
- Check API keys are valid
- Review `MIN_EVENT_SCORE` threshold (lower for testing: `0.3`)
- Check logs for source fetcher errors
- Verify `ENABLE_SCHEDULER=true`

**Railway volume disappeared:**
- Volumes can be accidentally deleted
- Always backup SQLite database periodically
- Re-upload MaxMind database if volume is recreated

### Frontend Issues

**"WebSocket connection failed":**
- Verify `NEXT_PUBLIC_WS_URL` uses `wss://` not `ws://`
- Check Railway backend is running
- Confirm `WS_ALLOWED_ORIGINS` includes Vercel URL
- Test WebSocket manually from browser console

**"Connection status stuck on connecting":**
- Backend may not be running
- CORS/origin mismatch
- Check backend logs for connection rejection

**Environment variables not updating:**
- Vercel requires redeployment after env var changes
- Clear browser cache
- Check correct deployment environment (Production vs Preview)

### CORS Issues

**WebSocket origin blocked:**

Update Railway environment variables:
```bash
WS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-frontend-git-branch.vercel.app
```

Note: Vercel creates preview deployments with different URLs for each branch/PR.

## Monitoring and Maintenance

### Backend Monitoring

**Railway Dashboard:**
- CPU and memory usage
- Deployment logs
- Volume usage

**Key Metrics:**
- Poll cycle duration (should be < 30 seconds)
- Number of events inserted per cycle
- WebSocket connection count
- Database size (should stay under 100MB for 24-hour window)

### Frontend Monitoring

**Vercel Dashboard:**
- Build status
- Deployment logs
- Bandwidth usage
- Function invocations (if using serverless functions)

### Database Maintenance

SQLite database is automatically pruned every poll cycle (removes events older than 24 hours).

**Manual cleanup if needed:**
```bash
railway run bash
sqlite3 /data/events.db
sqlite> DELETE FROM events WHERE datetime(ts) < datetime('now', '-24 hours');
sqlite> VACUUM;
sqlite> .quit
```

### Updating Dependencies

**Backend:**
```bash
cd backend
pip install -U fastapi uvicorn pydantic-settings httpx aiosqlite apscheduler
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
npm update
npm audit fix
```

Test locally before deploying updates.

## Cost Estimation

### Railway (Free Tier)

- $5 USD in free credits per month
- Backend typically uses < $3/month with light traffic
- 1GB volume included

### Vercel (Hobby Tier)

- Free for personal projects
- Unlimited deployments
- 100GB bandwidth per month
- Should handle moderate traffic easily

### API Costs

- **AbuseIPDB**: Free tier (1,000 requests/day) is sufficient for 60-second polls
- **GreyNoise**: Community tier (10,000 requests/month) is sufficient
- **Cloudflare Radar**: Public API is free

**Total estimated cost: $0-5 USD/month**

## Security Best Practices

1. **Never commit API keys** to repository
2. **Use Railway/Vercel environment variables** for secrets
3. **Restrict `WS_ALLOWED_ORIGINS`** to your frontend domain only
4. **Enable HTTPS/WSS** in production (automatic on Railway/Vercel)
5. **Rotate API keys periodically**
6. **Monitor usage** to detect abuse
7. **Keep dependencies updated** for security patches

## Backup Strategy

### Database Backup

Download SQLite database periodically:

```bash
railway run bash -c "cat /data/events.db" > backup-$(date +%Y%m%d).db
```

### Configuration Backup

Export environment variables from Railway/Vercel dashboards and store securely.

### Code Backup

Ensure GitHub repository is backed up or mirrored.

## Scaling Considerations

If traffic grows beyond free-tier limits:

1. **Horizontal backend scaling**: Not supported with SQLite
   - Switch to PostgreSQL on Railway
   - Update `db.py` to use async PostgreSQL driver
   
2. **Rate limiting**: Add rate limiting middleware to backend

3. **Caching**: Add Redis for snapshot caching

4. **CDN**: Vercel automatically uses CDN for static assets

5. **Event cap**: Lower `EVENT_TTL_HOURS` or implement pagination

## Support

For deployment issues:
- Railway: https://help.railway.app
- Vercel: https://vercel.com/support
- GitHub Issues: [Your repository issues page]

---

**Deployment Checklist:**

Backend (Railway):
- [ ] Project created and connected to GitHub
- [ ] Persistent volume created and mounted at `/data`
- [ ] MaxMind database uploaded to volume
- [ ] Environment variables configured
- [ ] Backend deployed successfully
- [ ] Health endpoint returns 200
- [ ] WebSocket endpoint accessible

Frontend (Vercel):
- [ ] Project created and connected to GitHub
- [ ] Environment variables configured with Railway URL
- [ ] Frontend deployed successfully
- [ ] Globe renders correctly
- [ ] WebSocket connects successfully
- [ ] Events appear on dashboard

Post-Deployment:
- [ ] Backend `WS_ALLOWED_ORIGINS` updated with Vercel URL
- [ ] Backend redeployed with updated CORS settings
- [ ] CI/CD pipeline running successfully
- [ ] Monitoring enabled
- [ ] README updated with live demo URLs
