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

def state_to_out(s: GameState) -> StateOut:
    return StateOut(turn=s.turn, phase=s.phase.name, seed=s.seed)

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
