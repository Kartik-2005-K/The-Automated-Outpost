/**
 * components/NPCCard.jsx — Sidebar card for a single NPC.
 * Shows: stat bars, GOAP plan chain, social memory entries, status.
 */
import React from 'react'

const GOAL_COLORS = {
  Survive:        '#ff4d6d',
  Rest:           '#40a0ff',
  MaintainSocial: '#c084fc',
  RepairBase:     '#ff8c42',
  Idle:           '#4a6080',
}

function StatBar({ label, value, type }) {
  const pct = Math.max(0, Math.min(100, value))
  let fillClass = type
  let color = '#fff'
  if (type === 'energy') color = '#00c8ff'
  if (type === 'hunger') color = '#ffd700'
  if (type === 'social') color = '#e879f9'

  // Warning pulse when low
  const isLow = pct < 25

  return (
    <div className="stat-bar-row">
      <span className="stat-label">{label}</span>
      <div className="stat-track">
        <div
          className={`stat-fill ${fillClass}`}
          style={{
            width: `${pct}%`,
            boxShadow: isLow ? `0 0 6px ${color}` : 'none',
            animation: isLow ? 'pulse-dot 0.8s ease-in-out infinite' : 'none',
          }}
        />
      </div>
      <span className="stat-value" style={{ color: isLow ? color : undefined }}>
        {Math.round(pct)}
      </span>
    </div>
  )
}

function PlanChain({ plan, currentAction }) {
  if (!plan || plan.length === 0) {
    return <div className="empty-state">No plan</div>
  }
  return (
    <div className="plan-chain">
      {plan.map((action, i) => (
        <React.Fragment key={i}>
          <span
            className={`plan-action ${action === currentAction ? 'active' : ''}`}
            title={action}
          >
            {action}
          </span>
          {i < plan.length - 1 && <span className="plan-arrow">›</span>}
        </React.Fragment>
      ))}
    </div>
  )
}

function SocialScores({ scores }) {
  const entries = Object.entries(scores || {})
  if (entries.length === 0) return null
  return (
    <div className="social-score-row">
      {entries.map(([peerId, score]) => (
        <span
          key={peerId}
          className={`social-score-badge ${score >= 0 ? 'positive' : 'negative'}`}
          title={`Relationship with ${peerId}: ${score > 0 ? '+' : ''}${score.toFixed(2)}`}
        >
          {peerId.replace('npc_', '#')}: {score > 0 ? '+' : ''}{score.toFixed(1)}
        </span>
      ))}
    </div>
  )
}

export default function NPCCard({ npc }) {
  const goalColor = GOAL_COLORS[npc.current_goal] || '#4a6080'

  return (
    <div
      className="npc-card fade-in"
      style={{ '--npc-color': npc.color }}
      id={`npc-card-${npc.id}`}
    >
      {/* Header */}
      <div className="npc-header">
        <div
          className="npc-avatar"
          style={{ color: npc.color, borderColor: npc.color }}
        >
          {npc.name[0]}
        </div>
        <div>
          <div className="npc-name" style={{ color: npc.color }}>{npc.name}</div>
          <div style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            [{Math.round(npc.position?.[0] ?? 0)}, {Math.round(npc.position?.[1] ?? 0)}]
          </div>
        </div>
        <span
          className="npc-goal-badge"
          style={{ color: goalColor, borderColor: `${goalColor}55` }}
        >
          {npc.current_goal}
        </span>
      </div>

      {/* Stat bars */}
      <StatBar label="Energy" value={npc.stats?.energy ?? 0} type="energy" />
      <StatBar label="Hunger" value={npc.stats?.hunger ?? 0} type="hunger" />
      <StatBar label="Social" value={npc.stats?.social ?? 0} type="social" />

      {/* Action progress */}
      <div className="action-progress-track">
        <div
          className="action-progress-fill"
          style={{ width: `${(npc.action_progress ?? 0) * 100}%` }}
        />
      </div>

      {/* GOAP plan chain */}
      <PlanChain plan={npc.current_plan} currentAction={npc.current_action} />

      {/* Social scores */}
      <SocialScores scores={npc.social_scores} />

      {/* Status text */}
      <div className="npc-status" title={npc.status}>{npc.status || '...'}</div>
    </div>
  )
}
