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
  
  // State for MOVE_CAUTIOUS parameters
  const [cautiousTo, setCautiousTo] = useState<string>('')
  const [cautiousEdge, setCautiousEdge] = useState<[string, string] | null>(null)

  // ---------------------------------------------------------------------
  // Helpers for board visualisation
  // ---------------------------------------------------------------------
  function normEdge(a: string, b: string): [string, string] {
    return a < b ? [a, b] : [b, a]
  }

  function edgeEq(e1: [string, string], e2: [string, string]) {
    return (
      (e1[0] === e2[0] && e1[1] === e2[1]) ||
      (e1[0] === e2[1] && e1[1] === e2[0])
    )
  }

  function isDoorClosed(edge: [string, string]): boolean {
    if (!state?.doors) return false
    return state.doors.some(d => edgeEq(d, edge))
  }

  // Pretty-print an Action for UI lists
  function formatAction(a: ActionOut): string {
    let label = a.type
    const p: any = a.params || {}
    if (p.to) {
      label += ` to ${String(p.to)}`
    }
    if (
      p.noise_edge &&
      Array.isArray(p.noise_edge) &&
      p.noise_edge.length === 2
    ) {
      label += ` [${p.noise_edge[0]}-${p.noise_edge[1]}]`
    }
    return label
  }

  const playerNeighbors: [string, string][] = React.useMemo(() => {
    if (!state?.edges || !state.location) return []
    return state.edges.filter(e => e[0] === state.location || e[1] === state.location)
  }, [state?.edges, state?.location])

  // Compute open neighbors (not blocked by doors)
  const openNeighbors: string[] = React.useMemo(() => {
    if (!state?.location) return []
    return playerNeighbors
      .filter(edge => !isDoorClosed(edge))
      .map(edge => edge[0] === state?.location ? edge[1] : edge[0])
  }, [playerNeighbors, state?.location])

  // Compute incident edges for selected cautiousTo
  const incidentEdges: [string, string][] = React.useMemo(() => {
    if (!cautiousTo || !state?.edges) return []
    // Get all edges connected to the destination room that are not closed doors
    return state.edges
      .filter(edge => (edge[0] === cautiousTo || edge[1] === cautiousTo))
      .filter(edge => !isDoorClosed(edge))
  }, [cautiousTo, state?.edges])

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

  // Execute a chosen action (used by the "Do" buttons in the list)
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

  // Execute cautious move with selected parameters
  async function execCautiousMove() {
    if (loading || !cautiousTo || !cautiousEdge) return
    setLoading(true)
    setError(null)
    try {
      const next = await step('MOVE_CAUTIOUS', { 
        to: cautiousTo, 
        noise_edge: cautiousEdge 
      })
      setState(next)
      const a = await getActions()
      setActions(a)
      // Reset selections after move
      setCautiousTo('')
      setCautiousEdge(null)
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
            {/* Self-destruct system ------------------------------------------------ */}
            {'self_destruct_armed' in state && state.self_destruct_armed !== undefined && (
              <div>
                Self-destruct:{' '}
                {state.self_destruct_armed ? (
                  <b style={{ color: 'crimson' }}>
                    ARMED&nbsp;(timer&nbsp;
                    {state.destruction_timer ?? '?'}
                    )
                  </b>
                ) : (
                  <b style={{ color: 'green' }}>DISARMED</b>
                )}
              </div>
            )}
            {'intruder_burn_last' in state && state.intruder_burn_last !== undefined && (
              <div>Intruders burned last phase: <b>{state.intruder_burn_last}</b></div>
            )}
            {/* Game-over banner --------------------------------------------------- */}
            {'game_over' in state &&
              state.game_over !== undefined &&
              state.game_over && (
                <div>
                  Game Over:{' '}
                  <b style={{ color: state.win ? 'green' : 'crimson' }}>
                    {state.win ? 'WIN' : 'LOSS'}
                  </b>
                </div>
            )}
          </div>
        ) : (
          <div>Loading state…</div>
        )}
      </section>

      {/* ---------------------------------------------------------------- */}
      {/* Board visualisation                                             */}
      {/* ---------------------------------------------------------------- */}
      {state && (
        <section>
          <h2>Board</h2>
          {/* Neighbour doors */}
          <h3 style={{ marginBottom: 4 }}>Doors around {state.location}</h3>
          <ul>
            {playerNeighbors.map((edge, idx) => {
              const closed = isDoorClosed(edge)
              const neighbour = edge[0] === state.location ? edge[1] : edge[0]
              const actionType = closed ? 'OPEN_DOOR' : 'CLOSE_DOOR'
              const label = closed ? 'Open' : 'Close'
              return (
                <li key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>
                    {state.location} ↔ {neighbour}{' '}
                    {closed ? (
                      <span style={{ color: 'crimson' }}>(closed)</span>
                    ) : (
                      <span style={{ color: 'green' }}>(open)</span>
                    )}
                  </span>
                  <button
                    onClick={() => execAction({ type: actionType, params: { to: neighbour } })}
                    disabled={loading}
                  >
                    {label}
                  </button>
                </li>
              )
            })}
          </ul>

          {/* Cautious Move Form */}
          {openNeighbors.length > 0 && (
            <div style={{ marginTop: 16, padding: 12, border: '1px solid #ddd', borderRadius: 4 }}>
              <h3 style={{ marginTop: 0, marginBottom: 8 }}>Cautious Move</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div>
                  <label style={{ display: 'block', marginBottom: 4 }}>Destination:</label>
                  <select 
                    value={cautiousTo} 
                    onChange={(e) => {
                      setCautiousTo(e.target.value)
                      setCautiousEdge(null) // Reset edge when destination changes
                    }}
                    style={{ padding: 4, minWidth: 120 }}
                  >
                    <option value="">Select room</option>
                    {openNeighbors.map(room => (
                      <option key={room} value={room}>{room}</option>
                    ))}
                  </select>
                </div>
                
                {cautiousTo && incidentEdges.length > 0 && (
                  <div>
                    <label style={{ display: 'block', marginBottom: 4 }}>Noise edge:</label>
                    <select 
                      value={cautiousEdge ? `${cautiousEdge[0]}-${cautiousEdge[1]}` : ''}
                      onChange={(e) => {
                        const [a, b] = e.target.value.split('-')
                        setCautiousEdge(a && b ? [a, b] : null)
                      }}
                      style={{ padding: 4, minWidth: 120 }}
                    >
                      <option value="">Select edge</option>
                      {incidentEdges.map((edge, idx) => (
                        <option key={idx} value={`${edge[0]}-${edge[1]}`}>
                          {edge[0]} ↔ {edge[1]}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                
                <button 
                  onClick={execCautiousMove}
                  disabled={loading || !cautiousTo || !cautiousEdge}
                  style={{ marginTop: 8, alignSelf: 'flex-start' }}
                >
                  Move Cautiously
                </button>
              </div>
            </div>
          )}

          {/* Intruders */}
          {state.intruders && Object.keys(state.intruders).length > 0 && (
            <>
              <h3 style={{ marginBottom: 4 }}>Intruders</h3>
              <ul>
                {Object.entries(state.intruders).map(([room, hp]) => (
                  <li key={room}>
                    {room}: HP <b>{hp}</b>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Noise */}
          {(state.corridor_noise?.length || Object.keys(state.room_noise || {}).length) && (
            <>
              <h3 style={{ marginBottom: 4 }}>Noise</h3>
              {state.corridor_noise?.length && (
                <div>
                  <b>Corridors:</b>{' '}
                  {state.corridor_noise.map((n, i) => (
                    <span key={i} style={{ marginRight: 6 }}>
                      ({n.edge[0]}-{n.edge[1]}:{n.count})
                    </span>
                  ))}
                </div>
              )}
              {state.room_noise && Object.keys(state.room_noise).length > 0 && (
                <div>
                  <b>Rooms:</b>{' '}
                  {Object.entries(state.room_noise).map(([r, c]) => (
                    <span key={r} style={{ marginRight: 6 }}>
                      {r}:{c}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Fires ------------------------------------------------------------ */}
          {state.fires && state.fires.length > 0 && (
            <>
              <h3 style={{ marginBottom: 4 }}>Fires</h3>
              <div>
                {state.fires.map(r => (
                  <span key={r} style={{ marginRight: 6 }}>
                    {r}
                  </span>
                ))}
              </div>
            </>
          )}
        </section>
      )}

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
                <code>{formatAction(a)}</code>
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
