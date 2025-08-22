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
        
        # Apply END_PLAYER_PHASE to transition from PLAYER to ENEMY
        next_phase_action = Action(ActionType.END_PLAYER_PHASE)
        new_state = rules.apply(state, next_phase_action)
        
        # Verify phase changed to ENEMY
        self.assertEqual(new_state.phase, Phase.ENEMY,
                         "Phase should change to ENEMY after END_PLAYER_PHASE from PLAYER")
        
        # Verify health decreased by 1 due to intruder attack
        self.assertEqual(new_state.health, initial_health - 1, 
                         "Health should decrease by 1 when sharing room with intruder during ENEMY phase")
    
    def test_event_adds_noise(self):
        """Test that EVENT phase adds noise to the deterministic edge (A,B)."""
        # Create initial game state
        state = GameState()
        rules = Rules()
        
        # First transition to ENEMY phase via END_PLAYER_PHASE
        enemy_phase = rules.apply(state, Action(ActionType.END_PLAYER_PHASE))
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
        enemy_phase = rules.apply(state, Action(ActionType.END_PLAYER_PHASE))
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

    def test_event_intruder_moves_towards_player_respects_doors(self):
        """
        Intruder should move one step toward the player during EVENT phase
        if a path is open; it should stay put when the direct path is blocked
        by a closed door.
        """
        from src.n_r_ai.core.rules import _norm_edge  # local import to avoid circulars

        # --- Path OPEN ------------------------------------------------------
        # Player at A (default), intruder at C, no doors: expect move to B.
        state_open = GameState(intruders={"C"})
        rules = Rules()

        # Advance to EVENT phase (PLAYER -> ENEMY -> EVENT)
        enemy_phase = rules.apply(state_open, Action(ActionType.END_PLAYER_PHASE))
        event_phase = rules.apply(enemy_phase, Action(ActionType.NEXT_PHASE))

        # Intruder should now be in B
        self.assertIn("B", event_phase.intruders,
                      "Intruder should move from C to B when path is open")
        self.assertNotIn("C", event_phase.intruders,
                         "Intruder should leave C when path is open")

        # --- Path BLOCKED ---------------------------------------------------
        # Close door between B and C; intruder should remain in C.
        door_bc = _norm_edge("B", "C")
        state_blocked = GameState(intruders={"C"}, doors={door_bc})

        enemy_phase_blk = rules.apply(state_blocked, Action(ActionType.END_PLAYER_PHASE))
        event_phase_blk = rules.apply(enemy_phase_blk, Action(ActionType.NEXT_PHASE))

        self.assertIn("C", event_phase_blk.intruders,
                      "Intruder should stay in C when door (B,C) is closed")
        self.assertNotIn("B", event_phase_blk.intruders,
                         "Intruder should NOT enter B when door blocks the path")


if __name__ == '__main__':
    unittest.main()
