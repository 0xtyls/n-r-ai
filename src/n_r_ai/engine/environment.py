from __future__ import annotations
from typing import Any, Tuple
from ..core.game_state import GameState
from ..core.actions import Action
from ..core.rules import Rules
from .simulator import step as sim_step

class Environment:
    def __init__(self, rules: Rules | None = None) -> None:
        self.rules = rules or Rules()
        self.state = GameState()
        self.done = False

    def reset(self, seed: int | None = None) -> GameState:
        self.state = GameState(seed=seed)
        self.done = False
        return self.state

    def step(self, action: Action) -> Tuple[GameState, float, bool, dict[str, Any]]:
        if self.done:
            return self.state, 0.0, True, {}
        self.state = sim_step(self.state, action, self.rules)
        reward = 0.0
        self.done = False
        return self.state, reward, self.done, {}
