from __future__ import annotations
from typing import List, Dict, Tuple, Any, Set, Literal

from .game_state import GameState
from .actions import Action, ActionType
from .game_state import Phase  # enum
from .rng import RNG

# type aliases
Edge = Tuple[str, str]
NoiseTarget = Literal['corridor', 'room']
# attack resolution
AttackOutcome = Literal['miss', 'hit', 'crit', 'jam']


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

# ---------------------------------------------------------------------------#
# attack helpers                                                             #
# ---------------------------------------------------------------------------#

def _attack_outcome(attack_deck: int) -> AttackOutcome:
    """Deterministic placeholder for attack-deck resolution"""
    if attack_deck <= 0:
        return 'miss'
    if attack_deck % 13 == 0:
        return 'jam'
    if attack_deck % 7 == 0:
        return 'crit'
    return 'hit'

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

def _last_bullet_trigger(attack_deck_value: int) -> bool:
    """
    Deterministic stand-in for the “last-bullet” symbol on the Shoot die.
    Returns True when the provided value is a multiple of 5.
    (Uses deck counter before it is decremented.)
    """
    return attack_deck_value % 5 == 0 if attack_deck_value > 0 else False

class Rules:
    def legal_actions(self, state: GameState) -> List[Action]:
        actions: List[Action] = []

        if state.phase == Phase.PLAYER:
            # Movement options
            for neigh in _neighbors_open(state, state.player_room):
                actions.append(Action(ActionType.MOVE, {"to": neigh}))
                actions.append(Action(ActionType.MOVE_CAUTIOUS, {"to": neigh}))
            
            # Door actions
            for neigh in state.board.neighbors(state.player_room):
                edge = _norm_edge(state.player_room, neigh)
                if edge in state.doors:
                    actions.append(Action(ActionType.OPEN_DOOR, {"to": neigh}))
                else:
                    actions.append(Action(ActionType.CLOSE_DOOR, {"to": neigh}))
            
            # Combat actions --------------------------------------------------
            if state.player_room in state.intruders:
                # MELEE always possible
                actions.append(Action(ActionType.MELEE))
                # SHOOT only if gun ready & ammo
                if state.ammo > 0 and not state.weapon_jammed:
                    actions.append(Action(ActionType.SHOOT))
                    # BURST action (ranged attack) – same gating as SHOOT
                    actions.append(Action(ActionType.BURST))
            
            # Room actions ----------------------------------------------------
            room_type = state.board.room_types.get(state.player_room)
            if room_type in ('CONTROL', 'ARMORY', 'SURGERY', 'ENGINE', 'FIRE_CONTROL'):
                actions.append(Action(ActionType.USE_ROOM))
            if room_type == 'ENGINE':
                actions.append(Action(ActionType.ESCAPE))
            
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
        doors = set(state.doors)

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
        # Handle OPEN_DOOR / CLOSE_DOOR
        # --------------------------------------------------------------------
        elif action.type in (ActionType.OPEN_DOOR, ActionType.CLOSE_DOOR):
            to_room: str = action.params.get("to") if action.params else None  # type: ignore[attr-defined]
            if to_room is None or to_room not in state.board.neighbors(state.player_room):
                # illegal – ignore, treat as NOOP
                return state.next(turn=state.turn + 1)
            
            edge = _norm_edge(state.player_room, to_room)
            
            if action.type is ActionType.OPEN_DOOR:
                # Can only open if door is closed (edge is in doors)
                if edge in doors:
                    doors.remove(edge)
                    actions_in_turn += 1
            else:  # CLOSE_DOOR
                # Can only close if door is open (edge is not in doors)
                if edge not in doors:
                    doors.add(edge)
                    actions_in_turn += 1
            
            new_state = new_state.next(doors=doors)

        # --------------------------------------------------------------------
        # Handle SHOOT
        # --------------------------------------------------------------------
        elif action.type is ActionType.SHOOT:
            if (
                state.player_room in state.intruders
                and state.ammo > 0
                and not state.weapon_jammed
            ):
                new_intruders = dict(state.intruders)
                attack_deck_val = state.attack_deck

                # Determine outcome & last-bullet BEFORE deck decrement
                outcome = _attack_outcome(attack_deck_val)
                last_bullet = _last_bullet_trigger(attack_deck_val)

                # Decrement deck if possible
                new_attack_deck = max(attack_deck_val - 1, 0)

                # Consume ammo only on last-bullet symbol
                ammo_spent = 1 if last_bullet else 0
                ammo = max(state.ammo - ammo_spent, 0)

                weapon_jammed = state.weapon_jammed

                # Apply damage / jam according to outcome
                if outcome in ("hit", "crit"):
                    dmg = 1 if outcome == "hit" else 2
                    hp = new_intruders[state.player_room] - dmg
                    if hp <= 0:
                        new_intruders.pop(state.player_room)
                    else:
                        new_intruders[state.player_room] = hp
                elif outcome == "jam":
                    weapon_jammed = True
                # miss → nothing

                new_state = new_state.next(
                    intruders=new_intruders,
                    ammo=ammo,
                    attack_deck=new_attack_deck,
                    weapon_jammed=weapon_jammed,
                )
                actions_in_turn += 1

        # --------------------------------------------------------------------
        # Handle BURST (always consumes 1 ammo)
        # --------------------------------------------------------------------
        elif action.type is ActionType.BURST:
            if (
                state.player_room in state.intruders
                and state.ammo > 0
                and not state.weapon_jammed
            ):
                new_intruders = dict(state.intruders)
                attack_deck_val = state.attack_deck
                outcome = _attack_outcome(attack_deck_val)
                new_attack_deck = max(attack_deck_val - 1, 0)

                # BURST always spends exactly 1 ammo up-front
                ammo = state.ammo - 1

                weapon_jammed = state.weapon_jammed

                if outcome in ("hit", "crit"):
                    dmg = 1 if outcome == "hit" else 2
                    hp = new_intruders[state.player_room] - dmg
                    if hp <= 0:
                        new_intruders.pop(state.player_room)
                    else:
                        new_intruders[state.player_room] = hp
                elif outcome == "jam":
                    weapon_jammed = True

                new_state = new_state.next(
                    intruders=new_intruders,
                    ammo=ammo,
                    attack_deck=new_attack_deck,
                    weapon_jammed=weapon_jammed,
                )
                actions_in_turn += 1

        # --------------------------------------------------------------------
        # Handle MELEE
        # --------------------------------------------------------------------
        elif action.type is ActionType.MELEE:
            # Can melee if intruder shares the room
            if state.player_room in state.intruders:
                new_intruders = dict(state.intruders)
                hp = new_intruders[state.player_room]
                hp -= 1
                if hp <= 0:
                    new_intruders.pop(state.player_room)
                else:
                    new_intruders[state.player_room] = hp

                # Player takes 1 damage
                if health > 0:
                    health -= 1
                # Chance of serious wound (simplified deterministic)
                if health in (3, 1) and new_state.serious_wounds < 3:
                    new_state = new_state.next(serious_wounds=new_state.serious_wounds + 1)

                new_state = new_state.next(intruders=new_intruders)
                actions_in_turn += 1

        # --------------------------------------------------------------------
        # Handle USE_ROOM
        # --------------------------------------------------------------------
        elif action.type is ActionType.USE_ROOM:
            room_type = state.board.room_types.get(state.player_room)
            if room_type == 'CONTROL':
                # Toggle life support
                new_state = new_state.next(life_support_active=not state.life_support_active)
                actions_in_turn += 1
            elif room_type == 'ARMORY':
                updates: Dict[str, Any] = {}
                if new_state.ammo < new_state.ammo_max:
                    updates["ammo"] = new_state.ammo_max
                if new_state.weapon_jammed:
                    updates["weapon_jammed"] = False
                if updates:
                    new_state = new_state.next(**updates)
                actions_in_turn += 1
            elif room_type == 'SURGERY':
                updates: Dict[str, Any] = {}
                # heal 1 HP up to max 5
                if health < 5:
                    health += 1
                # clear 1 serious wound if any
                if new_state.serious_wounds > 0:
                    updates["serious_wounds"] = new_state.serious_wounds - 1
                # only apply if something changed
                if (updates or health != new_state.health):
                    if health != new_state.health:
                        updates["health"] = health
                    new_state = new_state.next(**updates) if updates else new_state
                    actions_in_turn += 1
            elif room_type == 'ENGINE':
                # Arm self-destruct if not already armed
                if not new_state.self_destruct_armed:
                    new_state = new_state.next(
                        self_destruct_armed=True,
                        destruction_timer=3,
                    )
                    actions_in_turn += 1
            elif room_type == 'FIRE_CONTROL':
                # Extinguish fire in the current room if present
                if state.player_room in new_state.fires:
                    new_fires = set(new_state.fires)
                    new_fires.discard(state.player_room)
                    new_state = new_state.next(fires=new_fires)
                # Using the console always consumes an action
                actions_in_turn += 1

        # --------------------------------------------------------------------
        # Handle ESCAPE
        # --------------------------------------------------------------------
        elif action.type is ActionType.ESCAPE:
            # Only legal in ENGINE (validated via legal_actions)
            new_state = new_state.next(game_over=True, win=True)
            actions_in_turn += 1

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

                # ------------------------------------------------------------------
                # Event card processing (v1.5 skeleton)
                # ------------------------------------------------------------------
                card_processed = False
                if new_state.event_deck_cards:
                    card = new_state.event_deck_cards[0]
                    remaining = new_state.event_deck_cards[1:]
                    new_state = new_state.next(
                        event_deck=len(remaining),
                        event_deck_cards=remaining,
                    )
                    card_processed = True

                    if card == "NOISE_CORRIDOR":
                        # same deterministic corridor noise logic
                        neighs = sorted(_neighbors_open(new_state, new_state.player_room))
                        if neighs:
                            edge = _norm_edge(new_state.player_room, neighs[0])
                            new_noise[edge] = new_noise.get(edge, 0) + 1
                    elif card == "NOISE_ROOM":
                        new_room_noise[new_state.player_room] = (
                            new_room_noise.get(new_state.player_room, 0) + 1
                        )
                    elif card == "BAG_DEV":
                        # increment dev counter and add an ADULT token
                        new_state = new_state.next(bag_dev_count=new_state.bag_dev_count + 1)
                        bag = dict(new_state.bag)
                        bag["ADULT"] = bag.get("ADULT", 0) + 1
                        new_state = new_state.next(bag=bag)
                    elif card == "SPAWN_FROM_BAG":
                        # deterministic draw: first token with count>0 sorted by name
                        if new_state.bag:
                            token_name = sorted(k for k, v in new_state.bag.items() if v > 0)[0]
                            new_bag = dict(new_state.bag)
                            new_bag[token_name] -= 1
                            if new_bag[token_name] <= 0:
                                new_bag.pop(token_name)
                            new_state = new_state.next(bag=new_bag)

                            if token_name == "ADULT":
                                if new_state.player_room not in new_state.intruders:
                                    intr = dict(new_state.intruders)
                                    intr[new_state.player_room] = 1
                                    new_state = new_state.next(intruders=intr)
                    elif card == "OXYGEN_LEAK":
                        # Life support immediately fails
                        new_state = new_state.next(life_support_active=False)
                    elif card == "FIRE_ROOM":
                        # Current room catches fire
                        new_fires = set(new_state.fires)
                        new_fires.add(new_state.player_room)
                        new_state = new_state.next(fires=new_fires)
                    # unknown card ids are ignored for now

                # ------------------------------------------------------------------
                # Fallback behaviour when no cards processed
                # ------------------------------------------------------------------
                if not card_processed:
                    if new_state.event_deck > 0:
                        new_state = new_state.next(event_deck=new_state.event_deck - 1)

                    # Add noise based on noise roll
                    noise_target = _noise_roll(state, action)
                    if noise_target == "corridor":
                        neighs = sorted(_neighbors_open(new_state, new_state.player_room))
                        if neighs:
                            edge = _norm_edge(new_state.player_room, neighs[0])
                            new_noise[edge] = new_noise.get(edge, 0) + 1
                    else:  # room noise
                        new_room_noise[new_state.player_room] = (
                            new_room_noise.get(new_state.player_room, 0) + 1
                        )

            # --- CLEANUP effects ---------------------------------------------
            elif phase == state.phase.__class__.CLEANUP:
                # self-destruct countdown
                timer = new_state.destruction_timer
                if new_state.self_destruct_armed and timer > 0:
                    timer -= 1
                new_state = new_state.next(
                    round=new_state.round + 1,
                    destruction_timer=timer,
                )

                # Check for self-destruct completion -> game lost
                if (
                    new_state.self_destruct_armed
                    and new_state.destruction_timer == 0
                    and not new_state.game_over
                ):
                    new_state = new_state.next(game_over=True, win=False)

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
            doors=doors,
        )

        return new_state
