from __future__ import annotations
from typing import List, Dict, Tuple, Any

from .game_state import GameState
from .actions import Action, ActionType

# type aliases
Edge = Tuple[str, str]


def _norm_edge(a: str, b: str) -> Edge:
    """
    Represent an undirected corridor edge in canonical (sorted) order so that
    ('A', 'B') and ('B', 'A') are treated as the same key.
    """
    return tuple(sorted((a, b)))  # type: ignore[return-value]

class Rules:
    def legal_actions(self, state: GameState) -> List[Action]:
        # Always allow NOOP (debug); real play uses MOVE/PASS.
        actions: List[Action] = []

        # Movement to neighbouring rooms.
        for neigh in state.board.neighbors(state.player_room):
            actions.append(Action(ActionType.MOVE, {"to": neigh}))
            # Cautious move (player may later pick which corridor gains noise)
            actions.append(Action(ActionType.MOVE_CAUTIOUS, {"to": neigh}))

        # Pass is always legal during the player phase.
        actions.append(Action(ActionType.PASS))

        # NOOP can be useful for testing
        actions.append(Action(ActionType.NOOP))

        return actions

    def apply(self, state: GameState, action: Action) -> GameState:
        # Shortcut for NOOP ---------------------------------------------------
        if action.type is ActionType.NOOP:
            return state.next(turn=state.turn + 1)

        new_state = state
        new_noise: Dict[Edge, int] = dict(state.noise)
        actions_in_turn = state.actions_in_turn

        # --------------------------------------------------------------------
        # Handle MOVE / MOVE_CAUTIOUS
        # --------------------------------------------------------------------
        if action.type in (ActionType.MOVE, ActionType.MOVE_CAUTIOUS):
            to_room: str = action.params.get("to") if action.params else None  # type: ignore[attr-defined]
            if to_room is None or to_room not in state.board.neighbors(state.player_room):
                # illegal – ignore, treat as NOOP
                return state.next(turn=state.turn + 1)

            # Move the player
            new_state = new_state.next(player_room=to_room)
            actions_in_turn += 1

            # Noise placement
            if action.type is ActionType.MOVE:
                edge = _norm_edge(state.player_room, to_room)
                new_noise[edge] = new_noise.get(edge, 0) + 1
            else:  # MOVE_CAUTIOUS
                chosen_edge_param = None
                if action.params:
                    maybe_edge = action.params.get("noise_edge")
                    if isinstance(maybe_edge, (list, tuple)) and len(maybe_edge) == 2:
                        maybe_edge = _norm_edge(str(maybe_edge[0]), str(maybe_edge[1]))
                        if maybe_edge in state.board.edges:
                            chosen_edge_param = maybe_edge
                if chosen_edge_param:
                    new_noise[chosen_edge_param] = new_noise.get(chosen_edge_param, 0) + 1

        # --------------------------------------------------------------------
        # Handle PASS
        # --------------------------------------------------------------------
        elif action.type is ActionType.PASS:
            # Passing does not count as an action but ends the turn immediately.
            pass  # nothing else to do

        # --------------------------------------------------------------------
        # End-of-turn processing
        # --------------------------------------------------------------------
        end_turn = action.type is ActionType.PASS or actions_in_turn >= 2

        # Apply hazards if turn ends
        oxygen = new_state.oxygen
        health = new_state.health
        if end_turn:
            if not new_state.life_support_active and oxygen > 0:
                oxygen -= 1
            if new_state.player_room in new_state.fires and health > 0:
                health -= 1
            actions_in_turn = 0  # reset for next player turn

        # Build final state snapshot
        new_state = new_state.next(
            noise=new_noise,
            actions_in_turn=actions_in_turn,
            oxygen=oxygen,
            health=health,
            turn=state.turn + 1,
        )

        return new_state
