/**
 * components/EventPanel.jsx — Manual event trigger + active events display.
 */
import React, { useState } from 'react'

const EVENT_OPTIONS = [
  { value: 'power_failure',  label: '⚡ Power Failure' },
  { value: 'toxic_spill',    label: '☠️ Toxic Spill' },
  { value: 'food_shortage',  label: '🥫 Food Shortage' },
  { value: 'meteor_strike',  label: '☄️ Meteor Strike' },
  { value: 'dust_storm',     label: '🌪️ Dust Storm' },
]

async function triggerEvent(eventType) {
  try {
    const res = await fetch('http://localhost:8000/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: eventType }),
    })
    return res.ok
  } catch {
    return false
  }
}

export default function EventPanel({ events }) {
  const [selected, setSelected] = useState('power_failure')
  const [triggering, setTriggering] = useState(false)
  const [feedback, setFeedback] = useState('')

  const handleTrigger = async () => {
    setTriggering(true)
    setFeedback('')
    const ok = await triggerEvent(selected)
    setFeedback(ok ? '✓ Triggered' : '✗ Backend offline')
    setTriggering(false)
    setTimeout(() => setFeedback(''), 2500)
  }

  return (
    <div className="event-panel">
      {/* Trigger row */}
      <div className="event-trigger-row">
        <select
          id="event-select"
          className="event-select"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          {EVENT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          id="btn-trigger-event"
          className="btn-trigger"
          onClick={handleTrigger}
          disabled={triggering}
        >
          {triggering ? '...' : 'FIRE'}
        </button>
      </div>

      {/* Feedback */}
      {feedback && (
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '10px',
          color: feedback.includes('✓') ? 'var(--accent-green)' : 'var(--accent-red)',
          padding: '4px 0',
          animation: 'fadeIn 0.2s ease',
        }}>
          {feedback}
        </div>
      )}

      {/* Active events */}
      <div className="active-events-list">
        {events.length === 0 ? (
          <div className="empty-state">No active events</div>
        ) : (
          events.map((event) => {
            const pct = (event.remaining_ticks / event.duration_ticks) * 100
            return (
              <div key={event.id} className="event-card" id={`event-${event.id}`}>
                <div className="event-name">{event.name}</div>
                <div className="event-desc">{event.description}</div>
                <div className="event-timer">
                  <div className="event-timer-bar">
                    <div
                      className="event-timer-fill"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="event-timer-label">{event.remaining_ticks}T</span>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
