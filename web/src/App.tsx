import React, { useEffect, useState } from 'react'
import { getState, getActions, step, type StateOut, type ActionOut } from './api'

export default function App() {
  const [state, setState] = useState<StateOut | null>(null)
  const [actions, setActions] = useState<ActionOut[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setError(null)
    try {
      const [s, a] = await Promise.all([getState(), getActions()])
      setState(s)
      setActions(a)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function onStep() {
    if (!actions.length) return
    setLoading(true)
    setError(null)
    try {
      const next = await step(actions[0].type, actions[0].params ?? undefined)
      setState(next)
      const a = await getActions()
      setActions(a)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 16, maxWidth: 640, margin: '0 auto' }}>
      <h1>n-r-ai</h1>
      <section>
        <h2>Game State</h2>
        {state ? (
          <div>
            <div>Turn: <b>{state.turn}</b></div>
            <div>Phase: <b>{state.phase}</b></div>
          </div>
        ) : (
          <div>Loading state…</div>
        )}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Actions</h2>
        {actions.length ? (
          <ul>
            {actions.map((a, i) => (
              <li key={i}>
                <code>{a.type}</code>
              </li>
            ))}
          </ul>
        ) : (
          <div>No available actions</div>
        )}
      </section>

      <div style={{ marginTop: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={onStep} disabled={!actions.length || loading}>
          {loading ? 'Stepping…' : 'Step first action'}
        </button>
        <button onClick={refresh}>Refresh</button>
        {error && <span style={{ color: 'crimson' }}>{error}</span>}
      </div>

      <hr style={{ margin: '24px 0' }} />
      <p style={{ color: '#555' }}>
        Dev server expects backend at <code>http://127.0.0.1:8000</code>. Override with <code>VITE_API_URL</code>.
      </p>
    </div>
  )
}
