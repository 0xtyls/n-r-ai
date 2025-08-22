from __future__ import annotations
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Dict, Set, Tuple

from .board import Board, RoomId

class Phase(Enum):
    SETUP = auto()
    PLAYER = auto()
    ENEMY = auto()
    EVENT = auto()
    CLEANUP = auto()

@dataclass(frozen=True)
class GameState:
    # core bookkeeping
    turn: int = 0
    phase: Phase = Phase.PLAYER
    seed: int | None = None

    # board & tokens
    board: Board = field(
        default_factory=lambda: Board(
            rooms={"A", "B", "C"},
            edges={("A", "B"), ("B", "C")},
            room_types={"A": "DEFAULT", "B": "CONTROL", "C": "DEFAULT"},
        )
    )
    player_room: RoomId = "A"

    # player resources / hazards
    oxygen: int = 5
    health: int = 5
    ammo: int = 3

    # per-turn counter
    actions_in_turn: int = 0

    # global systems
    life_support_active: bool = True

    # hazards state
    fires: Set[RoomId] = field(default_factory=set)
    noise: Dict[Tuple[RoomId, RoomId], int] = field(default_factory=dict)
    # per-room noise markers (separate from corridor noise)
    room_noise: Dict[RoomId, int] = field(default_factory=dict)
    # closed / blocked doors (undirected edges); movement & noise cannot cross
    doors: Set[Tuple[RoomId, RoomId]] = field(default_factory=set)

    # --- new v1.1 fields ----------------------------------------------------
    round: int = 1
    # Intruders tracked as room → HP
    intruders: Dict[RoomId, int] = field(default_factory=dict)
    event_deck: int = 10
    bag_dev_count: int = 0
    intruder_burn_last: int = 0
    # stub for future attack resolution
    attack_deck: int = 10

    def next(self, **changes: Any) -> "GameState":
        return replace(self, **changes)
