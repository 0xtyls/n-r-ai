import React, { useEffect, useState, useMemo, useRef } from 'react'
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
  
  // New UI state for enhanced interactions
  const [cautiousMode, setCautiousMode] = useState(false)
  const cautiousFormRef = useRef<HTMLDivElement | null>(null)

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

  // Build a map of noise counts keyed by "a|b" for easier lookup
  function buildNoiseMap(): Record<string, number> {
    const result: Record<string, number> = {}
    if (!state?.corridor_noise) return result
    
    for (const item of state.corridor_noise) {
      const key = `${item.edge[0]}|${item.edge[1]}`
      result[key] = item.count
    }
    return result
  }

  // Check if player can move to a destination
  function canMoveTo(dest: string): boolean {
    if (!state?.location) return false
    return openNeighbors.includes(dest)
  }

  // Find an action by type (and optionally params)
  function findAction(type: string, params?: Record<string, any>): ActionOut | undefined {
    if (!actions.length) return undefined
    
    if (!params) {
      return actions.find(a => a.type === type)
    }
    
    return actions.find(a => {
      if (a.type !== type) return false
      if (!a.params && !params) return true
      if (!a.params || !params) return false
      
      // Check if all params match
      for (const key in params) {
        if (params[key] !== a.params[key]) return false
      }
      return true
    })
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

  // Calculate room positions in a circle layout
  const roomPositions = useMemo(() => {
    if (!state?.rooms) return {}
    
    const width = 700
    const height = 380
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) * 0.35
    
    const positions: Record<string, {x: number, y: number}> = {}
    const rooms = [...state.rooms]
    
    rooms.forEach((room, i) => {
      const angle = (i / rooms.length) * 2 * Math.PI
      positions[room] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      }
    })
    
    return positions
  }, [state?.rooms])

  // Keyboard shortcuts
  useEffect(() => {
    if (!state || !actions.length) return
    
    function handleKeyDown(e: KeyboardEvent) {
      // Don't trigger shortcuts if an input is focused
      if (
        document.activeElement instanceof HTMLInputElement ||
        document.activeElement instanceof HTMLTextAreaElement ||
        document.activeElement instanceof HTMLSelectElement
      ) {
        return
      }
      
      switch (e.key.toLowerCase()) {
        case 'p': {
          const passAction = findAction('PASS')
          if (passAction) execAction(passAction)
          break
        }
        case 'e': {
          const endPhaseAction = findAction('END_PLAYER_PHASE')
          if (endPhaseAction) execAction(endPhaseAction)
          break
        }
        case 'n': {
          const nextPhaseAction = findAction('NEXT_PHASE')
          if (nextPhaseAction) execAction(nextPhaseAction)
          break
        }
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [state, actions])

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

  // Handle room click in the SVG board
  function handleRoomClick(roomId: string) {
    if (loading) return
    if (roomId === state?.location) return // No-op if clicking current room
    
    if (canMoveTo(roomId)) {
      if (cautiousMode) {
        // Set up cautious move form
        setCautiousTo(roomId)
        // Scroll to cautious form
        if (cautiousFormRef.current) {
          cautiousFormRef.current.scrollIntoView({ behavior: 'smooth' })
        }
      } else {
        // Regular move
        const moveAction = findAction('MOVE', { to: roomId })
        if (moveAction) execAction(moveAction)
      }
    }
  }

  // Handle edge click to toggle door
  function handleEdgeClick(edge: [string, string]) {
    if (loading) return
    
    // Only allow toggling doors connected to current location
    if (!state?.location || (edge[0] !== state.location && edge[1] !== state.location)) {
      return
    }
    
    const isClosed = isDoorClosed(edge)
    const neighbor = edge[0] === state.location ? edge[1] : edge[0]
    const actionType = isClosed ? 'OPEN_DOOR' : 'CLOSE_DOOR'
    
    const doorAction = findAction(actionType, { to: neighbor })
    if (doorAction) execAction(doorAction)
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
              <div>
                Oxygen: <b>{state.oxygen}</b>
                <div style={{ marginTop: 4, width: '100%', maxWidth: 200, height: 10, backgroundColor: '#eee', borderRadius: 5 }}>
                  <div 
                    style={{ 
                      width: `${(state.oxygen / 5) * 100}%`, 
                      height: '100%', 
                      backgroundColor: state.oxygen <= 1 ? 'crimson' : state.oxygen <= 2 ? 'orange' : 'green',
                      borderRadius: 5
                    }}
                  />
                </div>
              </div>
            )}
            {'health' in state && state.health !== undefined && (
              <div>
                Health: <b>{state.health}</b>
                <div style={{ marginTop: 4, width: '100%', maxWidth: 200, height: 10, backgroundColor: '#eee', borderRadius: 5 }}>
                  <div 
                    style={{ 
                      width: `${(state.health / 5) * 100}%`, 
                      height: '100%', 
                      backgroundColor: state.health <= 1 ? 'crimson' : state.health <= 2 ? 'orange' : 'green',
                      borderRadius: 5
                    }}
                  />
                </div>
              </div>
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
      {/* Interactive SVG Board                                            */}
      {/* ---------------------------------------------------------------- */}
      {state && (
        <section style={{ marginTop: 24 }}>
          <h2>Interactive Board</h2>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={cautiousMode} 
                onChange={(e) => setCautiousMode(e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Cautious Move Mode
            </label>
            <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
              {cautiousMode 
                ? "Click a room to set up a cautious move (you'll need to select a noise edge)" 
                : "Click a room to move directly (adds noise to the moved corridor)"}
            </div>
          </div>

          {/* Context Actions */}
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 8 }}>Context Actions</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {/* USE_ROOM if available */}
              {findAction('USE_ROOM') && (
                <button 
                  onClick={() => execAction(findAction('USE_ROOM')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  USE_ROOM
                </button>
              )}
              
              {/* SHOOT if available */}
              {findAction('SHOOT') && (
                <button 
                  onClick={() => execAction(findAction('SHOOT')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  SHOOT
                </button>
              )}
              
              {/* MELEE if available */}
              {findAction('MELEE') && (
                <button 
                  onClick={() => execAction(findAction('MELEE')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  MELEE
                </button>
              )}
              
              {/* PASS (always show) */}
              {findAction('PASS') && (
                <button 
                  onClick={() => execAction(findAction('PASS')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  PASS (p)
                </button>
              )}
              
              {/* END_PLAYER_PHASE if available */}
              {findAction('END_PLAYER_PHASE') && (
                <button 
                  onClick={() => execAction(findAction('END_PLAYER_PHASE')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  END_PHASE (e)
                </button>
              )}
              
              {/* NEXT_PHASE if available */}
              {findAction('NEXT_PHASE') && (
                <button 
                  onClick={() => execAction(findAction('NEXT_PHASE')!)}
                  disabled={loading}
                  style={{ padding: '4px 12px' }}
                >
                  NEXT_PHASE (n)
                </button>
              )}
            </div>
          </div>

          {/* SVG Board */}
          <div style={{ border: '1px solid #ddd', borderRadius: 4, padding: 8, backgroundColor: '#f9f9f9' }}>
            <svg width="700" height="380" viewBox="0 0 700 380">
              {/* Render edges */}
              {state.edges?.map((edge, idx) => {
                const source = roomPositions[edge[0]]
                const target = roomPositions[edge[1]]
                if (!source || !target) return null
                
                const isClosed = isDoorClosed(edge)
                const isConnectedToPlayer = edge[0] === state.location || edge[1] === state.location
                
                // Find noise count for this edge
                const noiseMap = buildNoiseMap()
                const noiseKey = `${edge[0]}|${edge[1]}`
                const noiseCount = noiseMap[noiseKey] || 0
                
                // Calculate midpoint for noise display
                const midX = (source.x + target.x) / 2
                const midY = (source.y + target.y) / 2
                
                return (
                  <g key={`edge-${idx}`}>
                    <line 
                      x1={source.x} 
                      y1={source.y} 
                      x2={target.x} 
                      y2={target.y}
                      stroke={isClosed ? 'crimson' : 'green'}
                      strokeWidth={3}
                      style={{ 
                        cursor: isConnectedToPlayer ? 'pointer' : 'default',
                        opacity: isClosed ? 0.7 : 1
                      }}
                      onClick={() => isConnectedToPlayer && handleEdgeClick(edge)}
                    />
                    
                    {/* Noise count */}
                    {noiseCount > 0 && (
                      <g transform={`translate(${midX}, ${midY})`}>
                        <circle r="12" fill="yellow" opacity="0.8" />
                        <text 
                          textAnchor="middle" 
                          dominantBaseline="middle"
                          fontSize="12"
                          fontWeight="bold"
                        >
                          {noiseCount}
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}
              
              {/* Render rooms */}
              {state.rooms?.map(roomId => {
                const pos = roomPositions[roomId]
                if (!pos) return null
                
                const isCurrentLocation = roomId === state.location
                const canMove = canMoveTo(roomId)
                const intruderHP = state.intruders?.[roomId]
                const hasFire = state.fires?.includes(roomId)
                const roomNoise = state.room_noise?.[roomId] || 0
                
                return (
                  <g 
                    key={`room-${roomId}`} 
                    transform={`translate(${pos.x}, ${pos.y})`}
                    style={{ cursor: canMove ? 'pointer' : 'default' }}
                    onClick={() => handleRoomClick(roomId)}
                  >
                    {/* Room circle */}
                    <circle 
                      r="22" 
                      fill={isCurrentLocation ? '#b3e0ff' : canMove ? '#e6f7ff' : 'white'} 
                      stroke={isCurrentLocation ? '#0066cc' : '#666'}
                      strokeWidth={isCurrentLocation ? 3 : 1}
                    />
                    
                    {/* Room ID */}
                    <text 
                      textAnchor="middle" 
                      dominantBaseline="middle"
                      fontSize="14"
                      fontWeight="bold"
                    >
                      {roomId}
                    </text>
                    
                    {/* Intruder badge */}
                    {intruderHP !== undefined && (
                      <g transform="translate(-18, -18)">
                        <circle r="10" fill="crimson" />
                        <text 
                          textAnchor="middle" 
                          dominantBaseline="middle"
                          fill="white"
                          fontSize="10"
                          fontWeight="bold"
                        >
                          {intruderHP}
                        </text>
                      </g>
                    )}
                    
                    {/* Fire badge */}
                    {hasFire && (
                      <g transform="translate(18, -18)">
                        <text 
                          textAnchor="middle" 
                          dominantBaseline="middle"
                          fontSize="14"
                        >
                          🔥
                        </text>
                      </g>
                    )}
                    
                    {/* Room noise badge */}
                    {roomNoise > 0 && (
                      <g transform="translate(18, 18)">
                        <circle r="10" fill="yellow" opacity="0.8" />
                        <text 
                          textAnchor="middle" 
                          dominantBaseline="middle"
                          fontSize="10"
                          fontWeight="bold"
                        >
                          {roomNoise}
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}
            </svg>
          </div>
          
          <div style={{ fontSize: 13, color: '#666', marginTop: 8 }}>
            Legend: Blue = current location, Light blue = reachable, Red lines = closed doors, Green lines = open doors
          </div>
        </section>
      )}

      {/* ---------------------------------------------------------------- */}
      {/* Board visualisation (original)                                   */}
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
            <div 
              ref={cautiousFormRef}
              style={{ marginTop: 16, padding: 12, border: '1px solid #ddd', borderRadius: 4 }}
            >
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
