from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..engine.environment import Environment
from ..core.actions import Action, ActionType
from ..core.rules import Rules
from ..core.game_state import GameState

app = FastAPI(title="n-r-ai server")

env = Environment(Rules())

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionIn(BaseModel):
    type: str
    params: Optional[Dict[str, Any]] = None

class ActionOut(BaseModel):
    type: str
    params: Optional[Dict[str, Any]] = None

class StateOut(BaseModel):
    turn: int
    phase: str
    seed: Optional[int] = None
    # extended fields for UI
    location: str
    oxygen: int
    health: int
    actions_in_turn: int
    life_support_active: bool
    # v1.2 additions
    round: int
    event_deck: int
    intruder_burn_last: int
    # v1.3 combat/armory
    ammo: int
    ammo_max: int
    weapon_jammed: bool
    serious_wounds: int

def state_to_out(s: GameState) -> StateOut:
    return StateOut(
        turn=s.turn,
        phase=s.phase.name,
        seed=s.seed,
        location=s.player_room,
        oxygen=s.oxygen,
        health=s.health,
        actions_in_turn=s.actions_in_turn,
        life_support_active=s.life_support_active,
        round=s.round,
        event_deck=s.event_deck,
        intruder_burn_last=s.intruder_burn_last,
        ammo=s.ammo,
        ammo_max=s.ammo_max,
        weapon_jammed=s.weapon_jammed,
        serious_wounds=s.serious_wounds,
    )

def action_to_out(a: Action) -> ActionOut:
    return ActionOut(type=a.type.name, params=dict(a.params) if a.params else None)

def parse_action(inp: ActionIn) -> Action:
    try:
        at = ActionType[inp.type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {inp.type}")
    return Action(at, inp.params)

@app.on_event("startup")
def _startup() -> None:
    env.reset()

@app.get("/api/state", response_model=StateOut)
def get_state() -> StateOut:
    return state_to_out(env.state)

@app.get("/api/actions", response_model=List[ActionOut])
def get_actions() -> List[ActionOut]:
    actions = env.rules.legal_actions(env.state)
    return [action_to_out(a) for a in actions]

@app.post("/api/step", response_model=StateOut)
def post_step(a: ActionIn) -> StateOut:
    action = parse_action(a)
    s, _, _, _ = env.step(action)
    return state_to_out(s)

# --- LLM integration ---------------------------------------------------------

from .llm import llm_choose_action  # noqa: E402


class LLMActIn(BaseModel):
    persona: Optional[str] = None
    temperature: Optional[float] = None


class LLMActOut(BaseModel):
    chosen: ActionOut
    rationale: str
    state: StateOut


@app.post("/api/llm_act", response_model=LLMActOut)
def post_llm_act(body: LLMActIn) -> LLMActOut:
    actions = env.rules.legal_actions(env.state)
    actions_payload = [
        {"type": a.type.name, "params": dict(a.params) if a.params else None}
        for a in actions
    ]
    state_summary = (
        f"turn={env.state.turn}, phase={env.state.phase.name}, seed={env.state.seed}"
    )

    try:
        res = llm_choose_action(
            state_summary,
            actions_payload,
            persona=body.persona,
            temperature=body.temperature,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    idx = res["pick"]
    rationale = res.get("rationale", "")
    chosen = actions[idx] if actions else Action(ActionType.NOOP)

    s, _, _, _ = env.step(chosen)

    return LLMActOut(
        chosen=action_to_out(chosen),
        rationale=rationale,
        state=state_to_out(s),
    )
