import React, { useEffect, useState } from 'react'
import {
  getState,
  getActions,
  step,
  llmAct,
  type StateOut,
  type ActionOut,
  type LLMActOut,
} from './api'

export default function App() {
  const [state, setState] = useState<StateOut | null>(null)
  const [actions, setActions] = useState<ActionOut[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [persona, setPersona] = useState('')
  const [llmLoading, setLlmLoading] = useState(false)
  const [llmResult, setLlmResult] = useState<LLMActOut | null>(null)

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

  // Execute a chosen action (used by the “Do” buttons in the list)
  async function execAction(action: ActionOut) {
    if (loading) return
    setLoading(true)
    setError(null)
    try {
      const next = await step(action.type, action.params ?? undefined)
      setState(next)
      const a = await getActions()
      setActions(a)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLoading(false)
    }
  }

  async function onLlmAct() {
    setError(null)
    setLlmResult(null)
    setLlmLoading(true)
    try {
      const res = await llmAct(persona || undefined, 0.7)
      setLlmResult(res)
      setState(res.state)
      const a = await getActions()
      setActions(a)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLlmLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 16, maxWidth: 720, margin: '0 auto' }}>
      <h1>n-r-ai</h1>

      <section>
        <h2>Game State</h2>
        {state ? (
          <div>
            <div>Turn: <b>{state.turn}</b></div>
            <div>Phase: <b>{state.phase}</b></div>
            {'location' in state && state.location !== undefined && (
              <div>Location: <b>{state.location}</b></div>
            )}
            {'oxygen' in state && state.oxygen !== undefined && (
              <div>Oxygen: <b>{state.oxygen}</b></div>
            )}
            {'health' in state && state.health !== undefined && (
              <div>Health: <b>{state.health}</b></div>
            )}
            {'life_support_active' in state && state.life_support_active !== undefined && (
              <div>
                Life support:{' '}
                <b style={{ color: state.life_support_active ? 'green' : 'crimson' }}>
                  {state.life_support_active ? 'ON' : 'OFF'}
                </b>
              </div>
            )}
            {'ammo' in state && state.ammo !== undefined && (
              <div>
                Ammo:{' '}
                <b>
                  {state.ammo}/{state.ammo_max ?? '?'}
                </b>{' '}
                {state.weapon_jammed && (
                  <span
                    style={{
                      marginLeft: 6,
                      padding: '2px 6px',
                      background: 'crimson',
                      color: 'white',
                      borderRadius: 4,
                      fontSize: 12,
                      verticalAlign: 'middle',
                    }}
                  >
                    JAMMED
                  </span>
                )}
              </div>
            )}
            {'serious_wounds' in state && state.serious_wounds !== undefined && (
              <div>Serious wounds: <b>{state.serious_wounds}</b></div>
            )}
            {'actions_in_turn' in state && state.actions_in_turn !== undefined && (
              <div>Actions this turn: <b>{state.actions_in_turn}</b></div>
            )}
            {'round' in state && state.round !== undefined && (
              <div>Round: <b>{state.round}</b></div>
            )}
            {'event_deck' in state && state.event_deck !== undefined && (
              <div>Event deck: <b>{state.event_deck}</b></div>
            )}
            {'intruder_burn_last' in state && state.intruder_burn_last !== undefined && (
              <div>Intruders burned last phase: <b>{state.intruder_burn_last}</b></div>
            )}
          </div>
        ) : (
          <div>Loading state…</div>
        )}
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Persona</h2>
        <textarea
          placeholder="Persona (optional)"
          value={persona}
          onChange={e => setPersona(e.target.value)}
          rows={3}
          style={{ width: '100%', fontFamily: 'inherit' }}
        />
      </section>

      <section style={{ marginTop: 16 }}>
        <h2>Actions</h2>
        {actions.length ? (
          <ul>
            {actions.map((a, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <code>{a.type}</code>
                <button
                  onClick={() => execAction(a)}
                  disabled={loading}
                >
                  Do
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div>No available actions</div>
        )}
      </section>

      <div style={{ marginTop: 16, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <button onClick={onStep} disabled={!actions.length || loading}>
          {loading ? 'Stepping…' : 'Step first action'}
        </button>
        <button onClick={refresh}>Refresh</button>
        <button onClick={onLlmAct} disabled={llmLoading}>
          {llmLoading ? 'LLM…' : 'LLM Act'}
        </button>
        {error && <span style={{ color: 'crimson' }}>{error}</span>}
      </div>

      {llmResult && (
        <div style={{ marginTop: 12, background: '#f7f7f7', padding: 12, borderRadius: 4 }}>
          <div>LLM chose action: <code>{llmResult.chosen.type}</code></div>
          {llmResult.rationale && (
            <div style={{ marginTop: 4, fontStyle: 'italic' }}>{llmResult.rationale}</div>
          )}
        </div>
      )}

      <hr style={{ margin: '24px 0' }} />
      <p style={{ color: '#555' }}>
        Backend: <code>http://127.0.0.1:8000</code> (override with <code>VITE_API_URL</code>). Set LLM env vars: <code>OPENAI_API_KEY</code>, optional <code>LLM_BASE_URL</code>, <code>LLM_MODEL</code>, <code>LLM_TEMPERATURE</code>.
      </p>
    </div>
  )
}
