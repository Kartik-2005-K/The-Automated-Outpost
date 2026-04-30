/**
 * components/DebugPanel.jsx — AI Brain debug overlay.
 * Shows each NPC's active goal, full plan, social scores, and global stats.
 */
import React from 'react'

const GOAL_COLORS = {
  Survive:        '#ff4d6d',
  Rest:           '#40a0ff',
  MaintainSocial: '#c084fc',
  RepairBase:     '#ff8c42',
  Idle:           '#4a6080',
}

export default function DebugPanel({ npcs, tick, baseIntegrity, events }) {
  return (
    <div className="debug-panel">
      {/* Global stats */}
      <div className="glass-card">
        <div className="debug-row">
          <span className="debug-key">SIM TICK</span>
          <span className="debug-val" id="debug-tick">#{tick}</span>
        </div>
        <div className="debug-row">
          <span className="debug-key">BASE INTEGRITY</span>
          <span className="debug-val" style={{
            color: baseIntegrity < 40 ? 'var(--accent-red)'
                 : baseIntegrity < 70 ? 'var(--accent-orange)'
                 : 'var(--accent-green)'
          }}>
            {Math.round(baseIntegrity)}%
          </span>
        </div>
        <div className="debug-row">
          <span className="debug-key">ACTIVE EVENTS</span>
          <span className="debug-val" style={{ color: events.length > 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
            {events.length}
          </span>
        </div>
        <div className="debug-row">
          <span className="debug-key">NPCS ONLINE</span>
          <span className="debug-val">{npcs.length}</span>
        </div>
      </div>

      {/* Per-NPC AI state */}
      {npcs.map((npc) => {
        const goalColor = GOAL_COLORS[npc.current_goal] || '#4a6080'
        const socialEntries = Object.entries(npc.social_scores || {})

        return (
          <div className="debug-npc-row" key={npc.id} id={`debug-npc-${npc.id}`}>
            <div className="debug-npc-name" style={{ color: npc.color }}>
              {npc.name}
              <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: 6 }}>
                @ [{Math.round(npc.position?.[0] ?? 0)}, {Math.round(npc.position?.[1] ?? 0)}]
              </span>
            </div>

            <div className="debug-npc-goal" style={{ color: goalColor }}>
              GOAL: {npc.current_goal}
            </div>

            <div className="debug-npc-plan">
              PLAN: {npc.current_plan?.length
                ? npc.current_plan.join(' → ')
                : 'idle'}
            </div>

            {/* Action progress */}
            <div style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              ACT: <span style={{ color: 'var(--accent-cyan)' }}>{npc.current_action}</span>
              {' '}({Math.round((npc.action_progress ?? 0) * 100)}%)
            </div>

            {/* Social scores */}
            {socialEntries.length > 0 && (
              <div className="social-score-row">
                {socialEntries.map(([peer, score]) => (
                  <span
                    key={peer}
                    className={`social-score-badge ${score >= 0 ? 'positive' : 'negative'}`}
                  >
                    {peer.replace('npc_', 'NPC#')}: {score > 0 ? '+' : ''}{score.toFixed(2)}
                  </span>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
