from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, Tuple, Dict

RoomId = str

@dataclass(frozen=True)
class Board:
    rooms: Set[RoomId]
    edges: Set[Tuple[RoomId, RoomId]]
    # Optional mapping from room id to a type/label (e.g., "CONTROL", "ARMORY").
    # Defaults to empty dict so existing construction code continues to work.
    room_types: Dict[RoomId, str] = field(default_factory=dict)

    def neighbors(self, r: RoomId) -> Set[RoomId]:
        return {b for a, b in self.edges if a == r} | {a for a, b in self.edges if b == r}
