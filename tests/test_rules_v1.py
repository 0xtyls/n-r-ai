import unittest
from src.n_r_ai.core.game_state import GameState
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules


class TestRulesV1(unittest.TestCase):
    def test_legal_actions_include_move_and_pass(self):
        """Test that legal actions from initial state include MOVE to neighbors and PASS."""
        # Create initial game state (default has player at room "A" with neighbors "B")
        state = GameState()
        rules = Rules()
        
        # Get legal actions
        actions = rules.legal_actions(state)
        
        # Check that MOVE to neighbor "B" exists
        move_actions = [a for a in actions if a.type == ActionType.MOVE]
        self.assertTrue(any(a.params.get('to') == 'B' for a in move_actions), 
                        "MOVE to room B should be a legal action")
        
        # Check that PASS exists
        pass_actions = [a for a in actions if a.type == ActionType.PASS]
        self.assertTrue(len(pass_actions) > 0, "PASS should be a legal action")
    
    def test_end_of_turn_oxygen_loss_when_life_support_off(self):
        """Test oxygen loss at end of turn when life support is inactive."""
        # Create game state with life support off
        state = GameState(life_support_active=False)
        rules = Rules()
        
        # Record initial oxygen
        initial_oxygen = state.oxygen
        
        # Perform MOVE action (to room B)
        move_action = Action(ActionType.MOVE, {"to": "B"})
        state = rules.apply(state, move_action)
        
        # Verify actions_in_turn increased
        self.assertEqual(state.actions_in_turn, 1, "actions_in_turn should be 1 after one action")
        
        # Perform PASS action to end turn
        pass_action = Action(ActionType.PASS)
        state = rules.apply(state, pass_action)
        
        # Verify oxygen decreased by 1
        self.assertEqual(state.oxygen, initial_oxygen - 1, 
                         "Oxygen should decrease by 1 when life support is inactive")
        
        # Verify actions_in_turn reset to 0
        self.assertEqual(state.actions_in_turn, 0, 
                         "actions_in_turn should reset to 0 after turn end")
    
    def test_end_of_turn_fire_damage(self):
        """Test health damage at end of turn when in a room with fire."""
        # Create game state with fire in player's room
        state = GameState(fires={"A"})  # Player starts in room "A"
        rules = Rules()
        
        # Record initial health
        initial_health = state.health
        
        # Perform PASS action to end turn
        pass_action = Action(ActionType.PASS)
        state = rules.apply(state, pass_action)
        
        # Verify health decreased by 1
        self.assertEqual(state.health, initial_health - 1, 
                         "Health should decrease by 1 when in a room with fire")


if __name__ == '__main__':
    unittest.main()
