import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules

class TestAmmoAndAttackDeck(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()
        # Basic state with player in room A
        self.initial_state = GameState(
            player_room="A",
            phase=Phase.PLAYER
        )

    def test_shoot_not_legal_with_zero_ammo(self):
        """Test that SHOOT action is not legal when ammo is 0, even if intruder is present."""
        # Create state with intruder in player's room but no ammo
        state = self.initial_state.next(
            intruders={"A": 2},  # Intruder with 2 HP in room A
            ammo=0               # No ammo
        )
        
        # Get legal actions
        legal_actions = self.rules.legal_actions(state)
        
        # Verify SHOOT is not available
        shoot_actions = [a for a in legal_actions if a.type == ActionType.SHOOT]
        self.assertEqual(len(shoot_actions), 0, "SHOOT should not be legal when ammo is 0")

    def test_shoot_consumes_ammo(self):
        """Test that SHOOT action consumes ammo with each shot."""
        # Create state with intruder in player's room and 3 ammo
        state = self.initial_state.next(
            intruders={"A": 2},  # Intruder with 2 HP in room A
            ammo=3,              # 3 ammo
            attack_deck=10       # Plenty of attack cards
        )
        
        # Verify SHOOT action is available
        legal_actions = self.rules.legal_actions(state)
        shoot_actions = [a for a in legal_actions if a.type == ActionType.SHOOT]
        self.assertEqual(len(shoot_actions), 1, "Should have SHOOT action available")
        
        # Shoot once
        shoot_action = shoot_actions[0]
        state_after_shoot = self.rules.apply(state, shoot_action)
        
        # Verify ammo decreased by 1
        self.assertEqual(state_after_shoot.ammo, 2, "Ammo should decrease by 1 after SHOOT")
        
        # Shoot again
        state_after_second_shoot = self.rules.apply(state_after_shoot, shoot_action)
        
        # Verify ammo decreased again
        self.assertEqual(state_after_second_shoot.ammo, 1, "Ammo should decrease by 1 after second SHOOT")

    def test_no_damage_with_empty_attack_deck(self):
        """Test that SHOOT consumes ammo but doesn't damage intruder when attack_deck is 0."""
        # Create state with intruder, ammo, but empty attack deck
        state = self.initial_state.next(
            intruders={"A": 2},  # Intruder with 2 HP in room A
            ammo=3,              # 3 ammo
            attack_deck=0        # Empty attack deck
        )
        
        # Verify SHOOT action is available (ammo > 0 and intruder present)
        legal_actions = self.rules.legal_actions(state)
        shoot_actions = [a for a in legal_actions if a.type == ActionType.SHOOT]
        self.assertEqual(len(shoot_actions), 1, "Should have SHOOT action available with ammo > 0")
        
        # Shoot once
        shoot_action = shoot_actions[0]
        state_after_shoot = self.rules.apply(state, shoot_action)
        
        # Verify ammo decreased
        self.assertEqual(state_after_shoot.ammo, 2, "Ammo should decrease after SHOOT")
        
        # Verify intruder HP unchanged (no damage with empty attack deck)
        self.assertEqual(state_after_shoot.intruders.get("A", 0), 2, 
                         "Intruder HP should remain unchanged with empty attack deck")
        
        # Verify attack_deck remains at 0
        self.assertEqual(state_after_shoot.attack_deck, 0, "Attack deck should remain empty")

    def test_reload_enables_shoot(self):
        """Armory reload (USE_ROOM in room C) should replenish ammo and make SHOOT legal."""
        # Start in Armory (room C) with 0 ammo and an intruder present
        state = self.initial_state.next(
            player_room="C",
            intruders={"C": 1},
            ammo=0
        )

        # SHOOT must not be legal with 0 ammo
        legal = self.rules.legal_actions(state)
        self.assertEqual(
            [a for a in legal if a.type == ActionType.SHOOT],
            [],
            "SHOOT should not be legal when ammo is 0"
        )

        # USE_ROOM (reload) should be available in Armory
        use_room_actions = [a for a in legal if a.type == ActionType.USE_ROOM]
        self.assertEqual(len(use_room_actions), 1, "USE_ROOM should be available in Armory")

        # Apply reload
        state_after_reload = self.rules.apply(state, use_room_actions[0])

        # After reload, ammo should be at max
        self.assertEqual(
            state_after_reload.ammo,
            state_after_reload.ammo_max,
            "Ammo should be refilled to ammo_max after reload"
        )

        # SHOOT should now be legal
        legal_after_reload = self.rules.legal_actions(state_after_reload)
        self.assertTrue(
            any(a.type == ActionType.SHOOT for a in legal_after_reload),
            "SHOOT should be legal after reloading in Armory"
        )

    # ------------------------------------------------------------------ #
    # New tests for crits and jams (attack table)                        #
    # ------------------------------------------------------------------ #

    def test_shoot_crit_deals_two_damage(self):
        """Attack-deck value divisible by 7 (but not 13) triggers critical hit (2 dmg)."""
        state = self.initial_state.next(
            intruders={"A": 2},  # HP 2 intruder
            ammo=3,
            attack_deck=14       # 14 % 7 == 0 → crit
        )

        legal = self.rules.legal_actions(state)
        shoot = [a for a in legal if a.type == ActionType.SHOOT][0]

        s1 = self.rules.apply(state, shoot)

        # Intruder should be gone after 2 dmg
        self.assertNotIn("A", s1.intruders,
                         "Crit should deal 2 damage and eliminate HP=2 intruder")

    def test_shoot_jam_sets_jammed_and_blocks_shoot(self):
        """Attack-deck value divisible by 13 triggers weapon jam; SHOOT then blocked until cleared."""
        state = self.initial_state.next(
            intruders={"A": 2},
            ammo=2,
            attack_deck=13       # 13 % 13 == 0 → jam
        )

        # First shoot – triggers jam
        shoot = [a for a in self.rules.legal_actions(state) if a.type == ActionType.SHOOT][0]
        s1 = self.rules.apply(state, shoot)

        # Ammo spent, no damage done
        self.assertEqual(s1.ammo, 1, "Ammo should drop by 1")
        self.assertEqual(s1.intruders.get("A", 0), 2, "No damage on jammed shot")
        self.assertTrue(s1.weapon_jammed, "Gun should be jammed after jam outcome")

        # SHOOT should now be illegal
        self.assertFalse(any(a.type == ActionType.SHOOT
                             for a in self.rules.legal_actions(s1)),
                         "SHOOT should be unavailable while weapon is jammed")

        # Move to Armory (room C) and use room to clear jam
        s2 = s1.next(player_room="C")
        use_room = [a for a in self.rules.legal_actions(s2)
                    if a.type == ActionType.USE_ROOM][0]
        s3 = self.rules.apply(s2, use_room)

        # Jam cleared
        self.assertFalse(s3.weapon_jammed, "Armory reload should clear jammed weapon")

        # SHOOT legal again (ammo > 0 and not jammed)
        # Move back to the intruder's room (A) to validate legality
        s4 = s3.next(player_room="A")
        legal4 = self.rules.legal_actions(s4)
        self.assertTrue(any(a.type == ActionType.SHOOT for a in legal4),
                        "SHOOT should be legal again after clearing jam when sharing room with intruder")

if __name__ == "__main__":
    unittest.main()
