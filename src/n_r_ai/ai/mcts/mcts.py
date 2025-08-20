from __future__ import annotations
import math
import random
from typing import Callable
from .node import Node
from ...core.game_state import GameState
from ...core.actions import Action
from ...core.rules import Rules
from ...engine.simulator import step

Policy = Callable[[GameState, list[Action]], list[float]]

class MCTS:
    def __init__(self, rules: Rules | None = None, policy: Policy | None = None) -> None:
        self.rules = rules or Rules()
        self.policy = policy
        self.c_puct = 1.0
        self.root = Node()
        self.rng = random.Random()

    def search(self, state: GameState, iters: int = 100) -> Action:
        actions = self.rules.legal_actions(state)
        if len(actions) == 1:
            return actions[0]
        self.root = Node()
        for _ in range(iters):
            self._search_iter(state.next(), self.root, 0)
        best_action = None
        best_count = -1
        for action in actions:
            action_str = str(action)
            if action_str in self.root.children:
                child = self.root.children[action_str]
                if child.N > best_count:
                    best_count = child.N
                    best_action = action
        return best_action or actions[0]

    def _search_iter(self, state: GameState, node: Node, depth: int) -> float:
        if depth > 100:
            return 0.0
        actions = self.rules.legal_actions(state)
        if not actions:
            return 0.0
        if not node.children and node.N > 0:
            self._expand(node, state, actions)
        if not node.children:
            node.N += 1
            return self._simulate(state)
        action, child = self._select_child(node, actions)
        next_state = step(state, action, self.rules)
        value = self._search_iter(next_state, child, depth + 1)
        node.N += 1
        node.W += value
        node.Q = node.W / node.N
        return value

    def _expand(self, node: Node, state: GameState, actions: list[Action]) -> None:
        probs = None
        if self.policy:
            probs = self.policy(state, actions)
        for i, action in enumerate(actions):
            p = probs[i] if probs else 1.0 / len(actions)
            node.children[str(action)] = Node(action=action, P=p)

    def _select_child(self, node: Node, actions: list[Action]):
        best_score = float('-inf')
        best_action = None
        best_child = None
        for action in actions:
            action_str = str(action)
            if action_str not in node.children:
                continue
            child = node.children[action_str]
            exploit = child.Q
            explore = self.c_puct * child.P * math.sqrt(node.N) / (1 + child.N)
            score = exploit + explore
            if score > best_score:
                best_score = score
                best_action = action
                best_child = child
        if best_action is None and actions:
            best_action = actions[0]
            action_str = str(best_action)
            if action_str not in node.children:
                node.children[action_str] = Node(action=best_action)
            best_child = node.children[action_str]
        return best_action, best_child

    def _simulate(self, state: GameState) -> float:
        curr_state = state
        depth = 0
        while depth < 20:
            actions = self.rules.legal_actions(curr_state)
            if not actions:
                break
            action = self.rng.choice(actions)
            curr_state = step(curr_state, action, self.rules)
            depth += 1
        return 0.0
