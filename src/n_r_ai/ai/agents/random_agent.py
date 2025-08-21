from __future__ import annotations
import random
from ...core.rules import Rules
from ...core.actions import Action
from ...core.game_state import GameState

class RandomAgent:
    def __init__(self, rules: Rules | None = None, seed: int | None = None) -> None:
        self.rules = rules or Rules()
        self.rng = random.Random(seed)

    def act(self, state: GameState) -> Action:
        actions = self.rules.legal_actions(state)
        return self.rng.choice(actions)
