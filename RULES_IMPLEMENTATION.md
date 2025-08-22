# Rules Implementation Status Matrix

| Section | Level | Notes / Pointers |
|---------|-------|------------------|
| **1. Core Turn / Phases** | **Full** | Phase enum + cycle (PLAYER→ENEMY→EVENT→CLEANUP) in `core/game_state.py` & logic in `core/rules.py`.<br/>Tests: `tests/test_phases_v1.py` |
| **2. Movement & Noise** | **Partial** | MOVE / MOVE_CAUTIOUS, corridor vs room noise, deterministic `noise_roll` override. Lacks full dice table & technical corridors. Code: `rules.py` (`_noise_roll`, movement block). Tests: `test_rules_v1.py`, `test_noise_room_vs_corridor.py`. |
| **3. Doors** | **Full** | OPEN_DOOR / CLOSE_DOOR actions, movement blocking, noise cannot cross. Code: `rules.py` door handlers; state field `doors`. Tests: `test_actions_doors_shoot_room.py`. |
| **4. Encounters & Intruders** | **Partial** | Spawn on noise, intruder HP dict, EVENT path-finding 1-step, burn/fight damage. Missing attack dice, special types, multiple intruders per room. Code: `rules.py` encounter & EVENT sections. Tests: `test_encounter_v1.py`, `test_phases_v1.py`. |
| **5. Combat (Shooting / Melee)** | **Partial** | SHOOT action, ammo spend, simple hit if `attack_deck>0`, HP-1. No criticals, jamming, melee, serious wounds. Code: `rules.py` SHOOT block. Tests: `test_actions_doors_shoot_room.py`, `test_ammo_and_attack_deck.py`. |
| **6. Hazards (Oxygen / Fire)** | **Partial** | Oxygen loss when life support off, fire damage end-turn + intruder burn counter. No room destruction or lab fires. Code: end-turn block in `rules.py`. Tests: `test_rules_v1.py`. |
| **7. Event Deck** | **Partial** | Deck counter –, noise placement, intruder move. No full card effects. Code: EVENT phase in `rules.py`. Tests: `test_phases_v1.py`. |
| **8. Cleanup / Rounds** | **Full** | Round++ every CLEANUP, counters reset. Code: CLEANUP in `rules.py`; state.`round`. Tests: `test_phases_v1.py`. |
| **9. Rooms & Room Actions** | **Partial** | Board supports `room_types`; CONTROL room toggles life support via USE_ROOM. No other rooms (Armory, Surgery, etc.). Code: `board.py`, `rules.py` USE_ROOM block. Tests: `test_actions_doors_shoot_room.py`. |
| **10. Objectives** | **Not Implemented** | No objective cards, win checks. |
| **11. Items / Crafting** | **Not Implemented** | No item deck, crafting, inventory. |
| **12. Bag Development** | **Not Implemented** | Bag contents & draws absent. |
| **13. Escape / Win Conditions** | **Not Implemented** | No evacuation pods, hibernation, destruction timer. |
| **14. LLM Agents / UI** | **Partial** | LLMAgent persona play, REST API, React UI for manual actions. Lacks agent strategy & multiplayer lobby. Modules: `ai/agents/llm.py`, `server/`, `web/`. |

## Quick Navigation

| Module / Dir | Purpose |
|--------------|---------|
| `src/n_r_ai/core/` | Core game data-model & rules engine |
| `tests/` | High-level regression suite for mechanics above |
| `RULES.md` | Human-readable rules reference |
| `RULES_EXTRACT.txt` | Raw rulebook extraction (grep-able) |

## Next Priorities

1. Expand combat: attack dice table, melee, serious wounds.
2. Implement full Event cards & Bag development loop.
3. Add additional room types & actions (e.g., Armory – reload, Surgery – heal).
4. Objective & end-game flow (escape, destruction outcomes).
5. Enhance LLMAgent with rule-aware planning (use `core.rules.legal_actions`).
