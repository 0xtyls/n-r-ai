from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Mapping, Any

class ActionType(Enum):
    NOOP = auto()

@dataclass(frozen=True)
class Action:
    type: ActionType
    params: Mapping[str, Any] | None = None
