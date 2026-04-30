# 🚀 Vercel Deployment Guide

## Overview
The Automated Outpost can be deployed on Vercel using a monorepo structure:
- **Frontend**: React app served from Vercel
- **Backend**: FastAPI running as serverless functions
- **State**: Redis cache (optional, using Upstash)

---

## Step 1: Prepare Your Project

### Option A: Recommended - Use Upstash Redis (Serverless)

1. Go to [Upstash Redis](https://upstash.com/)
2. Create a free account and database
3. Copy your `REDIS_URL` from the dashboard
4. Save it for the environment variables step

### Option B: Alternative - In-Memory State (No Redis)

Edit `backend/redis_store.py` to always use in-memory storage (fallback mode).
This is simpler but state won't persist across function calls.

---

## Step 2: Connect to Vercel

### Prerequisites
- GitHub account with your repo
- Vercel account (free tier works)

### Connect Repository
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository: `Kartik-2005-K/The-Automated-Outpost`
4. Vercel will auto-detect the Next.js/monorepo structure

---

## Step 3: Configure Environment Variables

In the Vercel dashboard, go to your project → **Settings** → **Environment Variables**

Add these variables:

```
REDIS_URL = redis://<your-upstash-token>@<your-upstash-host>:<port>
VITE_API_URL = https://your-project.vercel.app/api
VERCEL_ENV = production
```

If using **in-memory only** (no Redis):
```
VITE_API_URL = https://your-project.vercel.app/api
VERCEL_ENV = production
```

---

## Step 4: Build Settings

Vercel should auto-detect, but verify:

- **Framework**: React (auto-detected)
- **Build Command**: `cd frontend && npm install && npm run build`
- **Output Directory**: `frontend/dist`
- **Install Command**: `npm install`

### Root Directory
If Vercel asks for root directory, leave blank (monorepo at root).

---

## Step 5: Deploy

1. Click **Deploy**
2. Vercel will:
   - Install frontend dependencies
   - Build React app
   - Bundle Python backend as serverless functions
   - Deploy to CDN

**Your project is live at**: `https://your-project.vercel.app`

---

## Step 6: Test Deployment

Open your deployed frontend and verify:

1. ✅ 3D scene renders
2. ✅ WebSocket connects (check browser console for errors)
3. ✅ API calls work (check Network tab)

### Common Issues

#### WebSocket Connection Fails
Vercel doesn't support persistent WebSocket connections. For real-time updates:

**Solution**: Switch from WebSocket to Server-Sent Events (SSE) or polling.

Edit `frontend/src/engine/WebSocketClient.js`:
```javascript
// Instead of WebSocket, use polling:
setInterval(() => {
  fetch('/api/state').then(r => r.json()).then(data => {
    // Update game state
  });
}, 1000); // Update every second
```

#### 502 Bad Gateway on `/api` calls
- Check Python requirements are installed
- Verify `api/main.py` handler exists
- Check environment variables in Vercel dashboard

#### Large Model Downloads Fail
The sentence-transformers embedding model (~80 MB) may timeout during build.

**Solution**: 
1. Use Upstash for persistent caching
2. Or download model locally and commit `.cache/` directory (if under 50 MB limit)

---

## Alternative: Use Vercel + External Python Server

If you want persistent backend without serverless limitations:

1. Deploy **frontend** on Vercel (normal)
2. Deploy **backend** separately on:
   - Railway.app (Python support)
   - Render.com (free tier available)
   - PythonAnywhere
   - AWS Lambda with RDS/ElastiCache

3. Update `VITE_API_URL` to external backend URL

---

## Performance Optimization

### Cold Starts
Serverless functions have ~1-2s cold start. To minimize:

1. Use requirements.txt efficiently:
   - Remove unused packages
   - `pip-tools` to freeze exact versions

2. Lazy load heavy modules in FastAPI routes

3. Cache embedding model in Upstash (persistent)

### File Size
Keep individual API functions under 50 MB uncompressed:
- Vercel's limit is 250 MB for all functions
- `sentence-transformers` is ~150 MB, so shared dependencies matter

---

## Running Locally with Vercel CLI

```bash
npm install -g vercel
vercel dev
```

This starts a local Vercel development environment that simulates serverless functions.

---

## Monitoring

Once deployed:

1. **Vercel Dashboard**: Check function execution logs
2. **Edge Network**: Monitor request latency
3. **Build Logs**: Debug build failures

---

## Next Steps

1. Test all AI features work on Vercel
2. Optimize WebSocket → polling if needed
3. Monitor cold start times
4. Set up GitHub → Vercel auto-deployment

**Questions?** Check [Vercel Docs](https://vercel.com/docs)

---
