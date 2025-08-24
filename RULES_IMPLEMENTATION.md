# Rules Implementation Status Matrix

| Section | Level | Notes / Pointers |
|---------|-------|------------------|
| **1. Core Turn / Phases** | **Full** | Phase enum + cycle (PLAYER→ENEMY→EVENT→CLEANUP) in `core/game_state.py` & logic in `core/rules.py`.<br/>Tests: `tests/test_phases_v1.py` |
| **2. Movement & Noise** | **Partial** | MOVE / MOVE_CAUTIOUS, corridor vs room noise, deterministic `noise_roll` override. Lacks full dice table & technical corridors. Code: `rules.py` (`_noise_roll`, movement block). Tests: `test_rules_v1.py`, `test_noise_room_vs_corridor.py`. |
| **3. Doors** | **Full** | OPEN_DOOR / CLOSE_DOOR actions, movement blocking, noise cannot cross. Code: `rules.py` door handlers; state field `doors`. Tests: `test_actions_doors_shoot_room.py`. |
| **4. Encounters & Intruders** | **Partial** | Spawn on noise, intruder HP dict, EVENT path-finding 1-step, burn/fight damage. Missing attack dice, special types, multiple intruders per room. Code: `rules.py` encounter & EVENT sections. Tests: `test_encounter_v1.py`, `test_phases_v1.py`. |
| **5. Combat (Shooting / Melee)** | **Partial** | Attack table via `_attack_outcome`: `hit` (-1 HP), `crit` (-2 HP), `jam` (sets `weapon_jammed`), `miss` (no dmg).<br/>SHOOT: spends ammo, draws outcome, blocked while `weapon_jammed`.<br/>MELEE: −1 HP to intruder, −1 health to player with simple serious-wound counter.<br/>State fields `weapon_jammed`, `serious_wounds`.<br/>Tests: `test_actions_doors_shoot_room.py`, `test_ammo_and_attack_deck.py`. |
| **6. Hazards (Oxygen / Fire)** | **Partial** | Oxygen loss when life support off, fire damage end-turn + intruder burn counter.<br/>New EVENT cards: **FIRE_ROOM** adds fire to player’s room, **OXYGEN_LEAK** instantly disables life support. No room destruction or lab fires yet. Code: end-turn & EVENT blocks in `rules.py`. Tests: `test_rules_v1.py`. |
| **7. Event Deck** | **Partial** | `event_deck_cards` skeleton implemented – EVENT phase now consumes top card and supports:<br/>• `NOISE_ROOM` • `NOISE_CORRIDOR` • `BAG_DEV` (also **adds one ADULT token to the bag**) • `SPAWN_FROM_BAG` • **`OXYGEN_LEAK` (life support OFF)** • **`FIRE_ROOM` (add fire to player’s room)**; graceful fallback when deck empty. Code: EVENT phase in `rules.py`. Tests: `test_phases_v1.py`, `test_event_bag_skeleton.py`. |
| **8. Cleanup / Rounds** | **Full** | Round++ every CLEANUP, counters reset. Code: CLEANUP in `rules.py`; state.`round`. Tests: `test_phases_v1.py`. |
| **9. Rooms & Room Actions** | **Partial** | `room_types`:  • CONTROL – toggle life support • ARMORY – reload to `ammo_max` **and clear jams** • **SURGERY – heal 1 HP (to max 5) and clear 1 serious wound** • **ENGINE – arm self-destruct (`self_destruct_armed=True`, `destruction_timer=3`) which decrements each CLEANUP**.  Code: `board.py`, `rules.py` USE_ROOM block & CLEANUP countdown. Tests: `test_actions_doors_shoot_room.py`, `test_rooms_surgery_engine.py`. |
| **10. Objectives** | **Not Implemented** | No objective cards, win checks. |
| **11. Items / Crafting** | **Not Implemented** | No item deck, crafting, inventory. |
| **12. Bag Development** | **Partial** | Simple `bag` dict (token→count) with deterministic draw order; `BAG_DEV` event increments `bag_dev_count` **and now adds an ADULT token**; `SPAWN_FROM_BAG` draws and spawns intruders. Code: EVENT phase in `rules.py`. Tests: `test_event_bag_skeleton.py`. |
| **13. Escape / Win Conditions** | **Partial** | **ESCAPE action** (legal only in ENGINE room) sets `game_over=True`, `win=True`.<br/>Self-destruct countdown: when timer hits 0 during CLEANUP, `game_over=True`, `win=False`. No evacuation pods / hibernation yet. Code: ESCAPE handler & CLEANUP block in `rules.py`. |
| **14. LLM Agents / UI** | **Partial** | LLMAgent persona play, REST API. UI now includes: parameterised **MOVE_CAUTIOUS** form (destination + noise-edge picker), door **Open/Close** controls, board visualisation of rooms, edges, door state, intruders, noise markers, **fires**, and **game-over banner**. Still lacks tactical agent logic, graph layout rendering, and multiplayer lobby. Modules: `ai/agents/llm.py`, `server/`, `web/`. |

## Quick Navigation

| Module / Dir | Purpose |
|--------------|---------|
| `src/n_r_ai/core/` | Core game data-model & rules engine |
| `tests/` | High-level regression suite for mechanics above |
| `RULES.md` | Human-readable rules reference |
| `RULES_EXTRACT.txt` | Raw rulebook extraction (grep-able) |

### Determinism note
Current dice / attack results use simple deterministic mappings (e.g., modulo checks in `_noise_roll` and `_attack_outcome`) to keep tests reproducible. Replace with true RNG tables once full rule fidelity is required.

## Next Priorities

1. Flesh out full attack dice tables (weapon types, ranged/energy), weapon jam clear actions, serious-wound decks.
2. Server/UI: improve board UX – proper graph layout, click-to-select rooms/edges, and dynamic highlights.
3. Implement full Event cards & Bag development loop.
4. Extend room roster and effects (current: Control, Armory, Surgery, Engine); add remaining special rooms and advanced effects.
5. Objective & end-game flow (escape pods, hibernation, destruction outcomes).
6. Enhance LLMAgent with rule-aware planning (use `core.rules.legal_actions`).
7. **Testing**: add dedicated tests for ESCAPE victory, OXYGEN_LEAK & FIRE_ROOM event handling, and self-destruct loss (timer = 0). UI now exposes end-game status; ensure regression coverage for these scenarios.
