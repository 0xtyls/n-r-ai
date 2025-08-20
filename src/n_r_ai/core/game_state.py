from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Any

class Phase(Enum):
    SETUP = auto()
    PLAYER = auto()
    ENEMY = auto()
    CLEANUP = auto()

@dataclass(frozen=True)
class GameState:
    turn: int = 0
    phase: Phase = Phase.SETUP
    seed: int | None = None

    def next(self, **changes: Any) -> "GameState":
        return replace(self, **changes)
