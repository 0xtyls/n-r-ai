from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Tuple

RoomId = str

@dataclass(frozen=True)
class Board:
    rooms: Set[RoomId]
    edges: Set[Tuple[RoomId, RoomId]]

    def neighbors(self, r: RoomId) -> Set[RoomId]:
        return {b for a, b in self.edges if a == r} | {a for a, b in self.edges if b == r}
