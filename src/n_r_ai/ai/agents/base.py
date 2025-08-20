from __future__ import annotations
from typing import Protocol
from ...core.game_state import GameState
from ...core.actions import Action

class Agent(Protocol):
    def act(self, state: GameState) -> Action: ...
