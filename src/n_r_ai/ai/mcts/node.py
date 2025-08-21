from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from ...core.actions import Action

@dataclass
class Node:
    action: Optional[Action] = None
    N: int = 0
    W: float = 0.0
    Q: float = 0.0
    P: float = 1.0
    children: Dict[str, "Node"] = field(default_factory=dict)
