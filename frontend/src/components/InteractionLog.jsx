/**
 * components/InteractionLog.jsx — Scrolling NPC interaction log.
 * Shows recent social events from the Zustand store logs buffer.
 */
import React from 'react'

export default function InteractionLog({ logs }) {
  if (!logs || logs.length === 0) {
    return <div className="empty-state">No interactions yet</div>
  }

  return (
    <div className="interaction-log" id="interaction-log">
      {logs.map((entry, i) => {
        const isPositive = entry.text?.includes('shared') || entry.text?.includes('friendly')
        const isNegative = entry.text?.includes('refused') || entry.text?.includes('tense') || entry.text?.includes('argue')
        const dotColor = isPositive ? 'var(--accent-green)'
                       : isNegative ? 'var(--accent-red)'
                       : 'var(--text-muted)'
        return (
          <div key={i} className="log-entry fade-in">
            <span className="log-tick">T{entry.tick ?? '?'}</span>
            <div
              className="log-sentiment"
              style={{ background: dotColor }}
            />
            <span className="log-text" title={entry.text}>{entry.text}</span>
          </div>
        )
      })}
    </div>
  )
}
