import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules, _norm_edge


class TestDoorsNoiseV1(unittest.TestCase):
    def test_cannot_move_through_closed_door(self):
        """Test that player cannot move through a closed door."""
        # Create a door on edge (A,B)
        door_edge = _norm_edge("A", "B")
        state = GameState(doors={door_edge})
        rules = Rules()
        
        # Verify legal actions don't include MOVE to B
        legal_actions = rules.legal_actions(state)
        move_actions = [a for a in legal_actions if a.type == ActionType.MOVE]
        self.assertFalse(any(a.params.get('to') == 'B' for a in move_actions),
                         "MOVE to B should not be legal when door is closed")
        
        # Try to apply MOVE to B anyway
        move_action = Action(ActionType.MOVE, {"to": "B"})
        new_state = rules.apply(state, move_action)
        
        # Verify player is still in room A
        self.assertEqual(new_state.player_room, "A", 
                         "Player should remain in room A when trying to move through closed door")
        
        # Verify turn incremented (NOOP behavior)
        self.assertEqual(new_state.turn, state.turn + 1, 
                         "Turn should increment when illegal move is treated as NOOP")
    
    def test_move_cautious_noise_ignored_if_edge_closed(self):
        """Test that noise is not added on closed edges during MOVE_CAUTIOUS."""
        # Part 1: Verify MOVE_CAUTIOUS is blocked by door on the movement path
        door_edge_ab = _norm_edge("A", "B")
        state = GameState(doors={door_edge_ab})
        rules = Rules()
        
        # Try to apply MOVE_CAUTIOUS to B
        move_action = Action(ActionType.MOVE_CAUTIOUS, {"to": "B"})
        new_state = rules.apply(state, move_action)
        
        # Verify player is still in room A (move blocked)
        self.assertEqual(new_state.player_room, "A", 
                         "Player should remain in room A when MOVE_CAUTIOUS through closed door")
        
        # Part 2: Verify noise not added on closed edge when specified as noise_edge
        # Create state with door on (B,C) but not on (A,B)
        door_edge_bc = _norm_edge("B", "C")
        state = GameState(doors={door_edge_bc})
        
        # Apply MOVE_CAUTIOUS from A to B with noise_edge=(B,C)
        move_action = Action(ActionType.MOVE_CAUTIOUS, {
            "to": "B", 
            "noise_edge": ["B", "C"]
        })
        new_state = rules.apply(state, move_action)
        
        # Verify player moved to B
        self.assertEqual(new_state.player_room, "B", 
                         "Player should move to B when path is open")
        
        # Verify no noise was added on closed edge (B,C)
        self.assertNotIn(door_edge_bc, new_state.noise, 
                         "Noise should not be added on closed edge (B,C)")
        
        # Verify actions_in_turn was incremented (move succeeded)
        self.assertEqual(new_state.actions_in_turn, 1, 
                         "actions_in_turn should be incremented for successful move")


if __name__ == '__main__':
    unittest.main()
