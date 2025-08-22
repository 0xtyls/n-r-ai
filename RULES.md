# N: R
### Unofficial Rules Reference for AI Development  

This document is **not** an official rulebook and is provided only to guide engine / agent implementation.*

---

## Finding full rules in `RULES_EXTRACT.txt`

`RULES_EXTRACT.txt` is a plain-text dump of the full rule-book PDF.  
Use a text search tool (`grep`, `rg`, an editor “find” panel, etc.) to jump from the short reference below to the complete wording in the extract.

| Topic | Helpful search terms in `RULES_EXTRACT.txt` |
|-------|---------------------------------------------|
| Round structure | `game round structure`, `PLAYER PHASE`, `INTRUDER PHASE`, `EVENT PHASE`, `cleanup phase`, `Bag Development` |
| Player turn & actions | `players' turns`, `RESOLVING ACTIONS`, `Actions List`, `Basic Action`, `Costing 1 Action card`, `Costing 2 Action cards`, `NOT IN COMBAT` |
| Movement | `MOVEMENT`, `Make a Move Cautiously` |
| Shooting | `shooting`, `Shooting is resolved in the following way` |
| Bursting | `bursting`, `Bursting is resolved in the following way` |
| Intruder movement | `Intruder Movement`, `INTRUDER MOVEMENT` |
| Objectives | `choosing an objective`, `OBJECTIVE AND MISSION TASK` |
| Escape & hibernation | `Hibernatorium`, `Make a Noise roll to Hibernate`, `Escape Shuttle` |
| Oxygen & fire | `Oxygen Loss`, `Fire Damage`, `Fire markers` |
| Lander & anti-aircraft | `LANDER`, `ANTI-AIRCRAFT` |
| Autodestruction | `AUTODESTRUCTION TOKEN` |

> **Tip – quick CLI look-ups (macOS/Linux)**  
> ```bash
> # basic POSIX grep
> grep -ni "PLAYER PHASE" RULES_EXTRACT.txt
>
> # ripgrep (if installed)
> rg -n "Shooting is resolved" RULES_EXTRACT.txt
> ```

---

## 1. Round Structure (exact order)

1. **Player Phase**  
   • Each player in turn order resolves a Player Turn.  
   • Continues until all players have *Passed*.  

2. **Intruder Phase**  
   • **Intruders Burning** – every Intruder in a Room with a Fire marker receives **1 Hit** (cannot by itself kill). If in the Nest, destroy **1 Egg**.  
   • **Intruder Attacks** – in each Room with at least one Character, the largest Intruder attacks the Character earliest in turn order.

3. **Event Phase**  
   • **Event Card Resolution**  
     – Apply Movement icons (see Intruder Movement rules).  
     – Resolve Main effect.  
     – Resolve Secondary effect (often adds Noise).  
     – Discard the card.  
   • **Bag Development** – draw one Intruder token from the bag, resolve its **front** per the Intruder Help sheet, place token on bottom of matching pile. (Queen death may alter effects.)

4. **Cleanup Phase**  
   • **Starting Player Change** – pass token clockwise.  
   • **Drawing Action Cards** – each Character draws up to 5 cards (reshuffle discard if deck empty).  
   • **Time Advancement** – advance Round marker; if marker enters a space with:  
     – **Lander token** → check Anti-Aircraft: if Inactive, Lander lands in Landing Zone; otherwise Lander destroyed.  
     – **Autodestruction token** → Facility explodes, all Characters in Facility (including Hibernating) die, all Rooms considered destroyed, all Intruders dead.  
     Start new Round or proceed to End-of-Game if track complete.

---

## 2. Player Turn Details

### 2.1 Sequence  
1. **Perform 2 Actions.**  
2. **Oxygen Loss** – if your Section’s Life Support is **Inactive**, lose 1 Oxygen.  
3. **Fire Damage** – if in a Room with a Fire marker, lose 1 Health Point.

You may, once per game, **choose your Objective** (before/after one of your Actions). This is *not* an Action.

### 2.2 Action Cost System  

| Cost | Actions (summary) | Combat Restriction* |
|------|-------------------|---------------------|
| 0    | • Play an Action card (resolve its text)  <br>• Pass | card-depend. |
| 1    | • **Move**  <br>• **Make a Move Cautiously** (choose corridor for Noise) <br>• **Fire a Shot** in the current Room <br>• **Fire a Burst** at an adjacent Corridor <br>• **Melee Attack** <br>• **Use an Item** <br>• **Activate the Robot** <br>• **Secure token** <br>• **Trade** <br>• **Use Tactical Gear** (Ammo/Oxygen/Grenade/Medpack) | some marked “Not in Combat” |
| 2    | • **Use the Room** (perform its Room action) | some Room actions combat-blocked |

\*Actions marked with the symbol in the rulebook may **not** be taken when the Character is *In Combat* (i.e., shares a Room with at least one Intruder).

---

## 3. Combat Mechanics

### 3.1 Shooting (Room)

1. Choose a Weapon (must have ≥1 Ammo token, no Malfunction).  
2. Deal **1 Hit** (place marker).  
3. Roll **Shoot die**:  
   • **Critical Kill** symbol – target dies.  
   • **Number (1-4)** – if result < current Hits on target, target dies.  
   • **“Last Bullet”** symbol – spend 1 Ammo token (flip or discard).  
4. Ammo is **not** normally spent; only the “last bullet” result consumes.  
5. Larvae and Queen use special health systems (not threshold-check).

### 3.2 Bursting (Corridor)

1. Choose Weapon (≥1 Ammo).  
2. **Spend 1 Ammo** immediately.  
3. Roll **Burst die** – number = Hits you may allocate to Intruders in chosen adjacent Corridor.  
4. Apply Hits of your choice, respecting:  
   • **Adult** dies at **1 Hit**.  
   • **Drone** requires **2 Hits** (cannot assign single Hit).  
5. Optional weapon effects may trigger on special symbol.

---

## 4. Intruder Movement (Event Card)

• Card shows icons for Intruder types and an orientation arrow.  
• Intruders of matching type in **Corridors** with that orientation move one step toward the **closest Character** (shortest path).  
• On entering a Room:  
  – If empty, follow Encounter rules.  
  – If containing Characters, perform Surprise / Attack sequences as per rulebook extract.

---

## 5. Bag Development (Event Phase Step 2)

1. Draw 1 Intruder token from the bag.  
2. Consult Intruder Help sheet, resolve effect (spawns, bag adds, etc.). Only front side matters.  
3. Discard token to bottom of its pile.  
4. If Queen is dead, some token effects change.

---

## 6. Cleanup Details

• After drawing to 5 cards, **reshuffle** discard pile into new deck if needed.  
• **Lander token** on Round track triggers landing check vs Anti-Aircraft tokens. Lander provides one Escape method once landed.  
• **Autodestruction token** triggers facility explosion as above.

---

## 7. Objectives, Escape & Victory

1. **Initial Deal** – each player is dealt:  
   – 1 **Private Objective** card (secret).  
   – 1 **Mission Objective** card (secret).  
   – A common **Mission Task** card is placed face-up on Round track.  
2. **Choosing Objective** – once per game, during your Turn (not an Action):  
   – Remove one Objective card; advance Objective Choice marker by 1; draw bonus Action cards equal to marker (first chooser draws 3, next 2, etc.).  
3. **Winning** – to win you must:  
   – Fulfil your chosen Objective **and**  
   – **Escape** the Facility alive via one of:  
     • **Lander** (if landed)  
     • **Hibernation** in Hibernatorium (Noise roll required)  
     • **Escape Shuttle** (if scenario provides)  
4. **Mission Task** may impose additional global victory/defeat constraints.  

---

## 8. Hazards Summary

* **Oxygen** – Each Character tracks Oxygen (dial).  
  – Lose 1 Oxygen at end of Turn if Life Support inactive in your Section.  
* **Fire** – Rooms may hold Fire markers.  
  – At Turn end Character suffers 1 Health in Fire Room.  
  – Intruders take Hits in Intruder Phase (cannot kill alone).  

---

## 9. Implementation Notes (mapping to `n_r_ai` code)

State fields to include in `GameState`:

```
round_number
phase  # enum{PLAYER, INTRUDER, EVENT, CLEANUP}
turn_order : list[player_id]
starting_player_idx
objective_choice_track : int
lander_status : enum{IN_ORBIT, LANDED, DESTROYED}
autodestruction_active : bool
time_track_pos
# Per-character
players: {
  id: {
    location_room_id,
    hand: list[card_id],
    deck: list[card_id],
    discard: list[card_id],
    objective_private,
    objective_mission,
    chosen_objective,
    oxygen,
    health,
    serious_wounds,
    contamination_cards,
  }
}
# Board
rooms: {room_id: {revealed, fire, slime, malfunction, item_counter}}
corridors: {(r1,r2): {noise, door_state}}
life_support: {section_id: bool_active}
intruder_bag: list[token]
event_deck: list[event_id]
intruders: {id:{type, room_id, hits}}
robot: {location, active}
```

Action enum suggestions (matching rules):

```
PLAY_CARD, PASS,
MOVE, MOVE_CAUTIOUS,
SHOOT, BURST, MELEE,
USE_ITEM, ACTIVATE_ROBOT,
SECURE, TRADE, USE_GEAR,
USE_ROOM
```

Randomness control: single seeded `rng` for  
• Shoot die, Burst die  
• Noise die / placement  
• Event deck draws, Bag draws, Attack cards  
• Card shuffles

Rule helpers:

```
Rules.legal_actions(state, player)
Rules.apply(state, action) -> state'
Encounter.resolve_move()
Combat.resolve_shoot(), Combat.resolve_burst()
Event.resolve(event_card)
BagDevelopment.resolve(token)
Cleanup.advance_round()
```

Keep pure functional transforms to support deterministic simulations and MCTS.

---

*End of rules reference.*
