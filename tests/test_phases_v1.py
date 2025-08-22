import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules


class TestPhasesV1(unittest.TestCase):
    def test_intruder_attack_on_enemy_phase(self):
        """Test that player takes damage when sharing a room with an intruder during ENEMY phase."""
        # Create initial game state with an intruder in player's room A
        state = GameState(intruders={"A"})  # Player starts in room "A" by default
        rules = Rules()
        
        # Record initial health
        initial_health = state.health
        
        # Apply NEXT_PHASE to transition from PLAYER to ENEMY
        next_phase_action = Action(ActionType.NEXT_PHASE)
        new_state = rules.apply(state, next_phase_action)
        
        # Verify phase changed to ENEMY
        self.assertEqual(new_state.phase, Phase.ENEMY, 
                         "Phase should change to ENEMY after NEXT_PHASE from PLAYER")
        
        # Verify health decreased by 1 due to intruder attack
        self.assertEqual(new_state.health, initial_health - 1, 
                         "Health should decrease by 1 when sharing room with intruder during ENEMY phase")
    
    def test_event_adds_noise(self):
        """Test that EVENT phase adds noise to the deterministic edge (A,B)."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        
        # First transition to ENEMY phase
        enemy_phase = rules.apply(state, Action(ActionType.NEXT_PHASE))
        self.assertEqual(enemy_phase.phase, Phase.ENEMY, "First phase transition should be to ENEMY")
        
        # Then transition to EVENT phase
        event_phase = rules.apply(enemy_phase, Action(ActionType.NEXT_PHASE))
        self.assertEqual(event_phase.phase, Phase.EVENT, "Second phase transition should be to EVENT")
        
        # Check that noise was added to edge (A,B) - this is deterministic based on implementation
        edge_key = tuple(sorted(("A", "B")))  # Normalized edge key
        self.assertIn(edge_key, event_phase.noise, "Noise should be added to edge (A,B)")
        self.assertEqual(event_phase.noise[edge_key], 1, 
                         "Noise count for edge (A,B) should be 1 after EVENT phase")
    
    def test_cleanup_increments_round(self):
        """Test that CLEANUP phase increments the round counter."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        initial_round = state.round
        
        # Cycle through phases: PLAYER -> ENEMY -> EVENT -> CLEANUP
        enemy_phase = rules.apply(state, Action(ActionType.NEXT_PHASE))
        event_phase = rules.apply(enemy_phase, Action(ActionType.NEXT_PHASE))
        cleanup_phase = rules.apply(event_phase, Action(ActionType.NEXT_PHASE))
        
        # Verify we reached CLEANUP phase
        self.assertEqual(cleanup_phase.phase, Phase.CLEANUP, 
                         "Should reach CLEANUP after three NEXT_PHASE actions")
        
        # Verify round incremented
        self.assertEqual(cleanup_phase.round, initial_round + 1, 
                         "Round should increment during CLEANUP phase")
        
        # Verify cycling back to PLAYER phase
        player_phase = rules.apply(cleanup_phase, Action(ActionType.NEXT_PHASE))
        self.assertEqual(player_phase.phase, Phase.PLAYER, 
                         "Should cycle back to PLAYER after CLEANUP")


if __name__ == '__main__':
    unittest.main()
