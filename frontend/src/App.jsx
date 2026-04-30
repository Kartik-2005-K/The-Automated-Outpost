/**
 * App.jsx — Root layout of the Automated Outpost frontend.
 *
 * Layout (3-column grid):
 *   [Left Panel: NPC Cards]  [Centre: 3D Scene]  [Right Panel: Debug + Events + Log]
 */
import React, { useEffect } from 'react'
import { useGameStore } from './store/useGameStore'
import { connectWebSocket } from './engine/WebSocketClient'
import Scene from './components/Scene'
import NPCCard from './components/NPCCard'
import EventPanel from './components/EventPanel'
import DebugPanel from './components/DebugPanel'
import InteractionLog from './components/InteractionLog'

function BaseIntegrityBar({ value }) {
  const color = value < 40 ? '#ff4d6d' : value < 70 ? '#ff8c42' : '#39ff85'
  return (
    <div className="base-integrity-bar">
      <div className="base-integrity-label">
        <span>⬡ BASE INTEGRITY</span>
        <span style={{ color }}>{Math.round(value)}%</span>
      </div>
      <div className="base-integrity-track">
        <div
          className="base-integrity-fill"
          style={{
            width: `${Math.max(0, Math.min(100, value))}%`,
            background: `linear-gradient(to right, ${color}88, ${color})`,
            boxShadow: `0 0 8px ${color}60`,
          }}
        />
      </div>
    </div>
  )
}

export default function App() {
  const {
    connected, tick, npcs, resources, events,
    baseIntegrity, showInfluence, showPaths, logs,
    toggleInfluence, togglePaths,
  } = useGameStore()

  useEffect(() => {
    connectWebSocket()
  }, [])

  return (
    <div className="app-shell">

      {/* ── Header ── */}
      <header className="header">
        <div>
          <div className="header-title">The Automated Outpost</div>
          <div className="header-subtitle">GOAP • A* Pathfinding • RAG Social Memory</div>
        </div>

        <div className="header-status">
          <div className={`status-pill ${connected ? 'online' : 'offline'}`}>
            <div className="status-dot" />
            {connected ? 'BRAIN ONLINE' : 'CONNECTING...'}
          </div>
          <div className="tick-counter">TICK #{tick}</div>
        </div>
      </header>

      {/* ── Left Panel: NPC Cards ── */}
      <aside className="panel-left" id="panel-left">
        <div className="panel-section-title">Crew — {npcs.length} NPCs</div>
        <BaseIntegrityBar value={baseIntegrity} />

        {npcs.length === 0 ? (
          <div className="empty-state">Waiting for backend...</div>
        ) : (
          npcs.map((npc) => <NPCCard key={npc.id} npc={npc} />)
        )}
      </aside>

      {/* ── Centre: 3D Canvas ── */}
      <main className="canvas-container" id="main-canvas">
        <Scene />

        {/* Canvas overlay buttons */}
        <div className="canvas-overlay">
          <button
            id="btn-toggle-influence"
            className={`overlay-btn ${showInfluence ? 'active' : ''}`}
            onClick={toggleInfluence}
          >
            {showInfluence ? '🔴 Influence ON' : '⬜ Influence OFF'}
          </button>
          <button
            id="btn-toggle-paths"
            className={`overlay-btn ${showPaths ? 'active' : ''}`}
            onClick={togglePaths}
          >
            {showPaths ? '🔵 Paths ON' : '⬜ Paths OFF'}
          </button>
        </div>
      </main>

      {/* ── Right Panel: Debug + Events + Log ── */}
      <aside className="panel-right" id="panel-right">

        {/* AI Debug */}
        <div className="panel-section-title">AI Brain — Debug</div>
        <DebugPanel
          npcs={npcs}
          tick={tick}
          baseIntegrity={baseIntegrity}
          events={events}
        />

        {/* Events */}
        <div className="panel-section-title" style={{ marginTop: 8 }}>Events</div>
        <EventPanel events={events} />

        {/* Social Interaction Log */}
        <div className="panel-section-title" style={{ marginTop: 8 }}>Social Log</div>
        <InteractionLog logs={logs} />
      </aside>

    </div>
  )
}
