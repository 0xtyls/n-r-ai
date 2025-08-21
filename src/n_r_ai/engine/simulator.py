from __future__ import annotations
from ..core.game_state import GameState
from ..core.actions import Action
from ..core.rules import Rules

def step(state: GameState, action: Action, rules: Rules) -> GameState:
    return rules.apply(state, action)
