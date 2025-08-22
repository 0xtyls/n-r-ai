import unittest
from src.n_r_ai.core.game_state import GameState
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules, _norm_edge


class TestEncounterV1(unittest.TestCase):
    def test_intruder_spawns_with_preexisting_noise(self):
        """Test that an intruder spawns when moving into a room with pre-existing noise on an incident edge."""
        # Create initial game state with player in A and noise on edge (A,B)
        edge_ab = _norm_edge("A", "B")
        state = GameState(noise={edge_ab: 1})
        rules = Rules()
        
        # Verify initial conditions
        self.assertEqual(state.player_room, "A", "Player should start in room A")
        self.assertEqual(state.noise[edge_ab], 1, "Edge (A,B) should have 1 noise")
        self.assertEqual(len(state.intruders), 0, "No intruders should exist initially")
        
        # Apply MOVE to B
        move_action = Action(ActionType.MOVE, {"to": "B"})
        new_state = rules.apply(state, move_action)
        
        # Verify player moved to B
        self.assertEqual(new_state.player_room, "B", "Player should have moved to room B")
        
        # Verify intruder spawned in B due to pre-existing noise
        self.assertIn("B", new_state.intruders, "Room B should have an intruder after move")
        self.assertEqual(len(new_state.intruders), 1, "Only one intruder should exist")

        # Verify noise on incident edge is cleared after encounter
        self.assertNotIn(edge_ab, new_state.noise,
                         "Noise on (A,B) should be cleared after encounter in room B")
    
    def test_no_intruder_without_preexisting_noise(self):
        """Test that moving to a room without pre-existing noise does NOT spawn an intruder."""
        # Create a state with player in B (as if they had already moved from A)
        state = GameState(player_room="B")
        rules = Rules()
        
        # Verify initial conditions
        self.assertEqual(state.player_room, "B", "Player should start in room B")
        self.assertEqual(len(state.intruders), 0, "No intruders should exist initially")
        
        # Apply MOVE to C
        move_action = Action(ActionType.MOVE, {"to": "C"})
        new_state = rules.apply(state, move_action)
        
        # Verify player moved to C
        self.assertEqual(new_state.player_room, "C", "Player should have moved to room C")
        
        # Verify NO intruder spawned in C (since there was no pre-existing noise)
        self.assertNotIn("C", new_state.intruders, "Room C should NOT have an intruder after move")
        self.assertEqual(len(new_state.intruders), 0, "No intruders should exist")


if __name__ == '__main__':
    unittest.main()
