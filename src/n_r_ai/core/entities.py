from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Player:
    id: int
    name: str = "P"

@dataclass(frozen=True)
class Marine:
    owner: int
    hp: int = 1

@dataclass(frozen=True)
class Enemy:
    kind: str
    hp: int = 1

@dataclass(frozen=True)
class Token:
    kind: str
    value: Any | None = None
