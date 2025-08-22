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

if __name__ == "__main__":
    unittest.main()
