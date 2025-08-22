from __future__ import annotations
from typing import List, Dict, Tuple, Any, Set, Literal

from .game_state import GameState
from .actions import Action, ActionType
from .game_state import Phase  # enum
from .rng import RNG

# type aliases
Edge = Tuple[str, str]
NoiseTarget = Literal['corridor', 'room']


def _norm_edge(a: str, b: str) -> Edge:
    """
    Represent an undirected corridor edge in canonical (sorted) order so that
    ('A', 'B') and ('B', 'A') are treated as the same key.
    """
    return tuple(sorted((a, b)))  # type: ignore[return-value]

# ---------------------------------------------------------------------------#
# helpers                                                                    #
# ---------------------------------------------------------------------------#

def _neighbors_open(state: GameState, room: str) -> List[str]:
    """
    Return neighbouring rooms reachable from `room`, i.e. board neighbours
    whose connecting edge is NOT blocked by a door.
    """
    neighs: List[str] = []
    for n in state.board.neighbors(room):
        if _norm_edge(room, n) not in state.doors:
            neighs.append(n)
    return neighs

def _noise_roll(state: GameState, action: Action) -> NoiseTarget:
    """
    Determine whether noise should be placed in a corridor or room.
    Can be overridden by action.params.get('noise_roll') if present.
    """
    # Check for override in action params
    if action.params and 'noise_roll' in action.params:
        roll_override = action.params.get('noise_roll')
        if roll_override in ('corridor', 'room'):
            return roll_override  # type: ignore
    
    # Default: place noise in the corridor that was used (legacy behaviour).
    # More elaborate dice logic can be added later.
    return 'corridor'

class Rules:
    def legal_actions(self, state: GameState) -> List[Action]:
        actions: List[Action] = []

        if state.phase == Phase.PLAYER:
            # Movement options
            for neigh in _neighbors_open(state, state.player_room):
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
        # copy of noise maps at the start of the step – used for encounter checks
        old_noise: Dict[Edge, int] = dict(state.noise)
        old_room_noise: Dict[str, int] = dict(state.room_noise)
        # mutated noise maps we will return with the new state
        new_noise: Dict[Edge, int] = dict(old_noise)
        new_room_noise: Dict[str, int] = dict(old_room_noise)
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
            # edge must be open
            move_edge = _norm_edge(state.player_room, to_room)
            if move_edge in state.doors:
                return state.next(turn=state.turn + 1)

            # Move the player
            new_state = new_state.next(player_room=to_room)
            actions_in_turn += 1

            # Noise placement based on noise roll
            noise_target = _noise_roll(state, action)
            
            if noise_target == 'corridor':
                # Add noise to corridor
                if action.type is ActionType.MOVE:
                    # Standard move: noise on the moved corridor
                    edge = move_edge
                    new_noise[edge] = new_noise.get(edge, 0) + 1
                else:  # MOVE_CAUTIOUS
                    # Cautious move: noise on chosen corridor
                    chosen_edge_param = None
                    if action.params:
                        maybe_edge = action.params.get("noise_edge")
                        if isinstance(maybe_edge, (list, tuple)) and len(maybe_edge) == 2:
                            maybe_edge = _norm_edge(str(maybe_edge[0]), str(maybe_edge[1]))
                            if maybe_edge in state.board.edges and maybe_edge not in state.doors:
                                chosen_edge_param = maybe_edge
                    if chosen_edge_param:
                        new_noise[chosen_edge_param] = new_noise.get(chosen_edge_param, 0) + 1
            else:  # noise_target == 'room'
                # Add noise to destination room
                new_room_noise[to_room] = new_room_noise.get(to_room, 0) + 1

            # --- encounter spawn check -------------------------------------
            if to_room not in new_state.intruders:
                # Check if destination room had room_noise OR any incident corridor had noise
                spawn = False
                
                # Check room noise
                if old_room_noise.get(to_room, 0) >= 1:
                    spawn = True
                
                # Check incident corridor noise
                if not spawn:
                    for a, b in old_noise:
                        if (a == to_room or b == to_room) and old_noise[(a, b)] >= 1:
                            spawn = True
                            break
                
                if spawn:
                    # Add intruder with 1 HP
                    new_intruders = dict(new_state.intruders)
                    new_intruders[to_room] = 1
                    new_state = new_state.next(intruders=new_intruders)
                    
                    # Clear all incident corridor noise
                    for a, b in list(new_noise):
                        if a == to_room or b == to_room:
                            new_noise.pop((a, b), None)
                    
                    # Clear room noise
                    if to_room in new_room_noise:
                        new_room_noise.pop(to_room)

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
            burn_total = len(set(new_state.intruders.keys()) & new_state.fires)
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
                burn_total = len(set(new_state.intruders.keys()) & new_state.fires)
                # damage to player if sharing room with intruder
                if new_state.player_room in new_state.intruders and health > 0:
                    health -= 1
                new_state = new_state.next(intruder_burn_last=burn_total)

            # --- EVENT effects ------------------------------------------------
            elif phase == state.phase.__class__.EVENT:
                # --- intruder movement towards player ----------------------
                from collections import deque

                # BFS distances from player
                dist: Dict[str, int] = {new_state.player_room: 0}
                q: deque[str] = deque([new_state.player_room])
                while q:
                    cur = q.popleft()
                    for nb in _neighbors_open(new_state, cur):
                        if nb not in dist:
                            dist[nb] = dist[cur] + 1
                            q.append(nb)

                # Track moved intruders with their HP
                moved_intruders: Dict[str, int] = {}
                dmg_event = 0
                
                # Move each intruder one step closer to player
                for room, hp in new_state.intruders.items():
                    # choose adjacent room that gets closer to player
                    best: str | None = None
                    best_d = dist.get(room, None)
                    if best_d is None:
                        # no path, stay
                        moved_intruders[room] = max(moved_intruders.get(room, 0), hp)
                        continue
                    
                    for nb in _neighbors_open(new_state, room):
                        if dist.get(nb, best_d + 1) < best_d:
                            best = nb
                            best_d = dist[nb]
                    
                    # Determine destination (best or stay put)
                    dest = best if best is not None else room
                    
                    # Handle merges by keeping max HP
                    moved_intruders[dest] = max(moved_intruders.get(dest, 0), hp)
                
                # Apply damage if intruder enters player's room
                if new_state.player_room in moved_intruders and health > 0:
                    dmg_event = 1
                health -= dmg_event

                # Update state with moved intruders
                new_state = new_state.next(intruders=moved_intruders)

                if new_state.event_deck > 0:
                    new_state = new_state.next(event_deck=new_state.event_deck - 1)
                
                # Add noise based on noise roll
                noise_target = _noise_roll(state, action)
                if noise_target == 'corridor':
                    # deterministic noise: lexicographically smallest neighbor edge
                    neighs = sorted(_neighbors_open(new_state, new_state.player_room))
                    if neighs:
                        edge = _norm_edge(new_state.player_room, neighs[0])
                        new_noise[edge] = new_noise.get(edge, 0) + 1
                else:  # noise_target == 'room'
                    # Add noise to player's room
                    new_room_noise[new_state.player_room] = new_room_noise.get(new_state.player_room, 0) + 1

            # --- CLEANUP effects ---------------------------------------------
            elif phase == state.phase.__class__.CLEANUP:
                new_state = new_state.next(round=new_state.round + 1)

            # after phase-specific updates new_state variables used below

        # Build final state snapshot
        new_state = new_state.next(
            noise=new_noise,
            room_noise=new_room_noise,
            actions_in_turn=actions_in_turn,
            oxygen=oxygen,
            health=health,
            turn=state.turn + 1,
            phase=phase,
        )

        return new_state
