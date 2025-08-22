import unittest
from src.n_r_ai.core.game_state import GameState
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules, _norm_edge


class TestNoiseRoomVsCorridor(unittest.TestCase):
    def test_move_noise_roll_corridor(self):
        """Test that MOVE with noise_roll='corridor' adds noise to the corridor, not the room."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        
        # Verify initial conditions
        self.assertEqual(state.player_room, "A", "Player should start in room A")
        
        # Apply MOVE to B with noise_roll='corridor'
        move_action = Action(ActionType.MOVE, {"to": "B", "noise_roll": "corridor"})
        new_state = rules.apply(state, move_action)
        
        # Verify player moved to B
        self.assertEqual(new_state.player_room, "B", "Player should have moved to room B")
        
        # Verify corridor noise was added to edge (A,B)
        edge_ab = _norm_edge("A", "B")
        self.assertIn(edge_ab, new_state.noise, "Edge (A,B) should have noise")
        self.assertEqual(new_state.noise[edge_ab], 1, "Edge (A,B) should have 1 noise")
        
        # Verify no room noise was added to room B
        self.assertNotIn("B", new_state.room_noise, "Room B should NOT have room noise")
    
    def test_move_noise_roll_room(self):
        """Test that MOVE with noise_roll='room' adds noise to the destination room, not the corridor."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        
        # Verify initial conditions
        self.assertEqual(state.player_room, "A", "Player should start in room A")
        
        # Apply MOVE to B with noise_roll='room'
        move_action = Action(ActionType.MOVE, {"to": "B", "noise_roll": "room"})
        new_state = rules.apply(state, move_action)
        
        # Verify player moved to B
        self.assertEqual(new_state.player_room, "B", "Player should have moved to room B")
        
        # Verify room noise was added to room B
        self.assertIn("B", new_state.room_noise, "Room B should have room noise")
        self.assertEqual(new_state.room_noise["B"], 1, "Room B should have 1 room noise")
        
        # Verify no corridor noise was added to edge (A,B)
        edge_ab = _norm_edge("A", "B")
        self.assertNotIn(edge_ab, new_state.noise, "Edge (A,B) should NOT have noise")
    
    def test_event_noise_roll_room_adds_room_noise(self):
        """Test that EVENT phase with noise_roll='room' adds noise to the player's room."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        
        # First transition to ENEMY phase via END_PLAYER_PHASE
        enemy_phase = rules.apply(state, Action(ActionType.END_PLAYER_PHASE))
        self.assertEqual(enemy_phase.phase, enemy_phase.phase.__class__.ENEMY, 
                         "First phase transition should be to ENEMY")
        
        # Then transition to EVENT phase with noise_roll='room'
        next_phase_action = Action(ActionType.NEXT_PHASE, {"noise_roll": "room"})
        event_phase = rules.apply(enemy_phase, next_phase_action)
        
        # Verify we reached EVENT phase
        self.assertEqual(event_phase.phase, event_phase.phase.__class__.EVENT, 
                         "Second phase transition should be to EVENT")
        
        # Verify room noise was added to player's room (A)
        self.assertIn("A", event_phase.room_noise, "Player's room (A) should have room noise")
        self.assertEqual(event_phase.room_noise["A"], 1, 
                         "Player's room (A) should have 1 room noise")
        
        # Verify no corridor noise was added
        edge_ab = _norm_edge("A", "B")
        self.assertNotIn(edge_ab, event_phase.noise, 
                         "No corridor noise should be added when noise_roll='room'")


if __name__ == '__main__':
    unittest.main()
