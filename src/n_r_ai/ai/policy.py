from __future__ import annotations
from typing import List
from ..core.game_state import GameState
from ..core.actions import Action

def uniform_policy(state: GameState, actions: List[Action]) -> List[float]:
    if not actions:
        return []
    p = 1.0 / len(actions)
    return [p] * len(actions)
