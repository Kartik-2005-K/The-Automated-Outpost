# 🛸 The Automated Outpost

> A real-time AI base-management simulation featuring GOAP planning, A* pathfinding with dynamic influence maps, and RAG-powered NPC social memory.

![Stack](https://img.shields.io/badge/Frontend-React+Three.js-61dafb?style=flat-square)
![Stack](https://img.shields.io/badge/Backend-FastAPI+Python-009688?style=flat-square)
![Stack](https://img.shields.io/badge/AI-GOAP+A*+RAG-ff6b35?style=flat-square)
![Stack](https://img.shields.io/badge/Cache-Redis-dc382d?style=flat-square)

---

## 🧠 Three Landmark AI Systems

| System | Technology | What it Does |
|--------|-----------|--------------|
| **GOAP Planner** | Custom A\* graph search | NPCs form multi-step action plans (e.g. Scavenge→CookMeal→Eat) dynamically based on world state |
| **A\* + Influence Map** | Pure Python pathfinding | 30×30 grid navigation; events stamp Gaussian danger gradients that inflate cell movement cost |
| **RAG Social Memory** | ChromaDB + sentence-transformers | NPC interactions are embedded as vectors; recalled sentiment scores modify future GOAP action costs |

---

## 🚀 Quick Start

### Option A: Docker (Recommended)

```bash
# Requires Docker + Docker Compose
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

### Option B: Manual Dev

#### 1. Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

uvicorn main:app --reload --port 8000
```

> **Note:** First startup downloads the `all-MiniLM-L6-v2` embedding model (~80 MB).  
> Redis is optional — the backend falls back to in-memory automatically.

#### 2. Frontend

```bash
# Requires Node.js 18+
# Download from: https://nodejs.org/

cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## 🗺️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Three.js + Zustand)                  │
│  ┌─────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │NPC Cards│ │  3D Scene    │ │ Debug/Events/Log     │  │
│  │stat bars│ │  isometric   │ │ GOAP plans, social   │  │
│  │plan chain│ │ path overlay │ │ scores, event fire   │  │
│  └─────────┘ └──────────────┘ └──────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                 WebSocket (JSON tick)
┌────────────────────────▼────────────────────────────────┐
│  Backend (FastAPI)                                      │
│                                                         │
│  Simulation Tick Loop (1/sec)                           │
│  ├── Goal Selection        ← NPC stats → priority queue │
│  ├── GOAP Planner          ← A* over world-state nodes  │
│  ├── A* Pathfinding        ← 30×30 grid + influence map │
│  ├── Social Memory (RAG)   ← ChromaDB vector queries    │
│  ├── Event System          ← Influence map stamping     │
│  └── Redis Cache           ← World state persistence    │
└─────────────────────────────────────────────────────────┘
```

---

## 🎮 How to Use

| Action | How |
|--------|-----|
| **Rotate camera** | Right-click drag |
| **Pan camera** | Middle-click drag |
| **Zoom** | Scroll wheel |
| **Toggle influence heatmap** | "Influence" button on canvas |
| **Toggle NPC path lines** | "Paths" button on canvas |
| **Fire an event** | Select from dropdown → FIRE |
| **See AI thinking** | Right panel → AI Brain Debug |
| **View REST API** | http://localhost:8000/docs |

---

## 📡 REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/state` | Full world state snapshot |
| `POST` | `/event` | Trigger a game event |
| `GET`  | `/npc/{id}/plan` | NPC's current GOAP plan |
| `GET`  | `/logs` | Recent social interactions |
| `WS`   | `/ws` | Live world state stream |

### Example: Trigger a toxic spill
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"event_type": "toxic_spill"}'
```

---

## 🗂️ Project Structure

```
automated-outpost/
├── backend/
│   ├── main.py              # FastAPI app, tick loop, NPC orchestration
│   ├── world_state.py       # All data models (NPC, Resource, Event, WorldState)
│   ├── redis_store.py       # Redis cache with in-memory fallback
│   ├── goap/
│   │   ├── actions.py       # 9 NPC actions with preconditions/effects/costs
│   │   ├── goals.py         # Priority-ordered goals with satisfaction lambdas
│   │   └── planner.py       # A*-based GOAP planning algorithm
│   ├── pathfinding/
│   │   ├── grid.py          # 30×30 walkability grid
│   │   ├── astar.py         # A* with influence-map cost integration
│   │   └── influence.py     # Gaussian danger propagation + decay
│   └── memory/
│       ├── social_memory.py # ChromaDB + sentence-transformers RAG
│       └── events_log.py    # Append-only interaction history
├── frontend/
│   └── src/
│       ├── App.jsx          # Root 3-column layout
│       ├── index.css        # Dark sci-fi design system
│       ├── store/
│       │   └── useGameStore.js  # Zustand global state
│       ├── engine/
│       │   └── WebSocketClient.js  # WS connection with backoff
│       └── components/
│           ├── Scene.jsx        # Three.js 3D isometric scene
│           ├── NPCCard.jsx      # Stat bars + plan chain + social scores
│           ├── EventPanel.jsx   # Manual event trigger + active events
│           ├── DebugPanel.jsx   # AI Brain debug overlay
│           └── InteractionLog.jsx  # Scrolling social event log
└── docker-compose.yml
```

---

## 🔬 Understanding the AI

### GOAP Example
If NPC **ARIA** has `hunger=15, has_food=false, has_fuel=true, energy=80`:

1. Goal selector picks `Survive` (hunger < 30 → critical)
2. GOAP planner runs A\* over world-state graph:
   - `Eat` precondition: `food_cooked=true` → not met
   - `CookMeal` precondition: `has_food=true` → not met  
   - `Scavenge` precondition: `energy>10` → ✓ met
   - Cheapest chain: **Scavenge** (cost 10) → **CookMeal** (cost 5) → **Eat** (cost 2)
3. ARIA pathfinds to nearest Food resource, picks it up, returns to base, cooks, eats.

### Social Memory Example
- Tick 40: BOLT refuses food to CODA → stored as `"BOLT refused to share food with CODA"` (sentiment -0.6)
- Tick 80: CODA's GOAP plans socializing. `recall(CODA, BOLT)` returns -0.6 → Socialize cost multiplied up
- CODA's planner now prefers other actions over approaching BOLT

---

## ⚙️ Configuration

Edit `backend/main.py` top constants:
```python
TICK_RATE_SECONDS = 1.0    # simulation speed
NPC_MOVE_SPEED    = 0.8    # tiles per tick
SOCIAL_DIST       = 3.0    # range for social interactions
RANDOM_EVENT_CHANCE = 0.03 # probability of random event per tick
```

---

## 📦 Dependencies

### Backend
- `fastapi` — async web framework
- `uvicorn` — ASGI server
- `chromadb` — in-memory vector database
- `sentence-transformers` — local text embeddings (no API key)
- `redis` — optional world state cache
- `numpy` — numerical operations
- `pydantic` — data validation

### Frontend
- `react` / `react-dom` — UI framework
- `three` — 3D rendering engine
- `@react-three/fiber` — React renderer for Three.js
- `@react-three/drei` — Three.js helpers (OrbitControls, Text, Line)
- `zustand` — lightweight state management
- `vite` — dev server and bundler
