from __future__ import annotations
from typing import List, Dict, Tuple, Any

from .game_state import GameState
from .actions import Action, ActionType
from .game_state import Phase  # enum

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
        actions: List[Action] = []

        if state.phase == Phase.PLAYER:
            # Movement options
            for neigh in state.board.neighbors(state.player_room):
                actions.append(Action(ActionType.MOVE, {"to": neigh}))
                actions.append(Action(ActionType.MOVE_CAUTIOUS, {"to": neigh}))
            # Pass is always legal
            actions.append(Action(ActionType.PASS))
            # Optionally end player phase when no pending actions
            if state.actions_in_turn == 0:
                actions.append(Action(ActionType.END_PLAYER_PHASE))
        else:
            # Non-player phases can only advance
            actions.append(Action(ActionType.NEXT_PHASE))

        # Always expose NOOP for debugging
        actions.append(Action(ActionType.NOOP))
        return actions

    def apply(self, state: GameState, action: Action) -> GameState:
        # Shortcut for NOOP ---------------------------------------------------
        if action.type is ActionType.NOOP:
            return state.next(turn=state.turn + 1)

        new_state = state
        # copy of noise map at the start of the step – used for encounter checks
        old_noise: Dict[Edge, int] = dict(state.noise)
        # mutated noise map we will return with the new state
        new_noise: Dict[Edge, int] = dict(old_noise)
        actions_in_turn = state.actions_in_turn
        phase = state.phase
        oxygen = new_state.oxygen
        health = new_state.health

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

            # --- encounter spawn check -------------------------------------
            if to_room not in new_state.intruders:
                # any incident edge that had noise >=1 **before** this move?
                spawn = False
                for a, b in old_noise:
                    if a == to_room or b == to_room:
                        if old_noise[(a, b)] >= 1:
                            spawn = True
                            break
                if spawn:
                    intruders = set(new_state.intruders)
                    intruders.add(to_room)
                    new_state = new_state.next(intruders=intruders)

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

        # --------------------------------------------------------------------
        # Handle explicit END_PLAYER_PHASE  ---------------------------------
        # --------------------------------------------------------------------
        if action.type is ActionType.END_PLAYER_PHASE:
            if state.phase != Phase.PLAYER or state.actions_in_turn != 0:
                # invalid use -> treat as NOOP
                return state.next(turn=state.turn + 1)

            phase = Phase.ENEMY
            # apply ENEMY effects
            burn_total = len(new_state.intruders & new_state.fires)
            if new_state.player_room in new_state.intruders and health > 0:
                health -= 1
            new_state = new_state.next(intruder_burn_last=burn_total)

        # --------------------------------------------------------------------
        # Handle NEXT_PHASE (phase transitions & effects)
        # --------------------------------------------------------------------
        if action.type is ActionType.NEXT_PHASE:
            # Only allowed if not in PLAYER phase
            if state.phase == Phase.PLAYER:
                return state.next(turn=state.turn + 1)

            def _cycle(p: Any) -> Any:
                if p == state.phase.__class__.PLAYER:
                    return state.phase.__class__.ENEMY
                if p == state.phase.__class__.ENEMY:
                    return state.phase.__class__.EVENT
                if p == state.phase.__class__.EVENT:
                    return state.phase.__class__.CLEANUP
                return state.phase.__class__.PLAYER  # from CLEANUP

            phase = _cycle(state.phase)

            # --- ENEMY effects ------------------------------------------------
            if phase == state.phase.__class__.ENEMY:
                burn_total = len(new_state.intruders & new_state.fires)
                # damage to player if sharing room with intruder
                if new_state.player_room in new_state.intruders and health > 0:
                    health -= 1
                new_state = new_state.next(intruder_burn_last=burn_total)

            # --- EVENT effects ------------------------------------------------
            elif phase == state.phase.__class__.EVENT:
                if new_state.event_deck > 0:
                    new_state = new_state.next(event_deck=new_state.event_deck - 1)
                # deterministic noise: lexicographically smallest neighbor edge
                neighs = sorted(new_state.board.neighbors(new_state.player_room))
                if neighs:
                    edge = _norm_edge(new_state.player_room, neighs[0])
                    new_noise[edge] = new_noise.get(edge, 0) + 1

            # --- CLEANUP effects ---------------------------------------------
            elif phase == state.phase.__class__.CLEANUP:
                new_state = new_state.next(round=new_state.round + 1)

            # after phase-specific updates new_state variables used below

        # Build final state snapshot
        new_state = new_state.next(
            noise=new_noise,
            actions_in_turn=actions_in_turn,
            oxygen=oxygen,
            health=health,
            turn=state.turn + 1,
            phase=phase,
        )

        return new_state
