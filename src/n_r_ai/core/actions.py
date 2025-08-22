from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Mapping, Any

class ActionType(Enum):
    NOOP = auto()
    PASS = auto()           # end turn early
    MOVE = auto()           # standard move (adds noise in the moved corridor)
    MOVE_CAUTIOUS = auto()  # cautious move (player chooses corridor for noise)
    END_PLAYER_PHASE = auto()  # explicitly finish player phase (allows NEXT_PHASE)
    NEXT_PHASE = auto()     # advance game phase (PLAYER→ENEMY→EVENT→CLEANUP→PLAYER)

@dataclass(frozen=True)
class Action:
    type: ActionType
    params: Mapping[str, Any] | None = None
