from __future__ import annotations
import json
from typing import Any, List, Mapping

from ...core.game_state import GameState
from ...core.actions import Action, ActionType
from ...core.rules import Rules
from ...engine.environment import Environment
from ...core.game_state import Phase
from ...core import game_state as gs
from ...core import actions as act

from ...server.llm import LLMConfig, llm_choose_action

class LLMAgent:
    def __init__(self, rules: Rules | None = None, persona: str | None = None, temperature: float | None = None) -> None:
        self.rules = rules or Rules()
        self.persona = persona
        self.temperature = temperature
        self.cfg = LLMConfig()

    def summarize_state(self, state: GameState) -> str:
        return f"turn={state.turn}, phase={state.phase.name}, seed={state.seed}"

    def summarize_actions(self, actions: List[Action]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, a in enumerate(actions):
            out.append({"index": i, "type": a.type.name, "params": dict(a.params) if a.params else None})
        return out

    def act(self, state: GameState) -> Action:
        actions = self.rules.legal_actions(state)
        if not actions:
            return Action(ActionType.NOOP)
        if len(actions) == 1:
            return actions[0]

        state_summary = self.summarize_state(state)
        actions_summary = self.summarize_actions(actions)

        res = llm_choose_action(state_summary, actions_summary, persona=self.persona, temperature=self.temperature, config=self.cfg)
        idx = res["pick"]
        return actions[idx]
