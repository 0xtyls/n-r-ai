from __future__ import annotations
from typing import List
from .game_state import GameState
from .actions import Action, ActionType

class Rules:
    def legal_actions(self, state: GameState) -> List[Action]:
        return [Action(ActionType.NOOP)]

    def apply(self, state: GameState, action: Action) -> GameState:
        return state.next(turn=state.turn + 1)
