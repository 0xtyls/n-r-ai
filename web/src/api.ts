const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export type StateOut = {
  turn: number
  phase: string
  seed?: number | null
  // extended fields (may be omitted by older server versions)
  location?: string
  oxygen?: number
  health?: number
  actions_in_turn?: number
  life_support_active?: boolean
  // v1.2 fields
  round?: number
  event_deck?: number
  intruder_burn_last?: number
  // v1.3 combat fields
  ammo?: number
  ammo_max?: number
  weapon_jammed?: boolean
  serious_wounds?: number
  // v1.4 board visualisation
  rooms?: string[]
  edges?: [string, string][]
  doors?: [string, string][]
  intruders?: Record<string, number>
  corridor_noise?: { edge: [string, string]; count: number }[]
  room_noise?: Record<string, number>
  // v1.5 bag development
  bag_dev_count?: number
  bag?: Record<string, number>
  // v1.6 self-destruct system
  self_destruct_armed?: boolean
  destruction_timer?: number
}

export type ActionOut = {
  type: string
  params?: Record<string, unknown> | null
}

export async function getState(): Promise<StateOut> {
  const res = await fetch(`${API_URL}/api/state`)
  if (!res.ok) throw new Error('Failed to fetch state')
  return res.json()
}

export async function getActions(): Promise<ActionOut[]> {
  const res = await fetch(`${API_URL}/api/actions`)
  if (!res.ok) throw new Error('Failed to fetch actions')
  return res.json()
}

export async function step(type: string, params?: Record<string, unknown>): Promise<StateOut> {
  const res = await fetch(`${API_URL}/api/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, params: params ?? null })
  })
  if (!res.ok) throw new Error('Failed to step')
  return res.json()
}

// ---------------------------------------------------------------------------
// LLM integration
// ---------------------------------------------------------------------------

export type LLMActOut = {
  chosen: ActionOut
  rationale: string
  state: StateOut
}

export async function llmAct(
  persona?: string,
  temperature?: number
): Promise<LLMActOut> {
  const res = await fetch(`${API_URL}/api/llm_act`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ persona: persona ?? null, temperature })
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    const msg =
      detail && detail.detail ? String(detail.detail) : 'LLM act failed'
    throw new Error(msg)
  }

  return res.json()
}
