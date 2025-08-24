import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules


class TestRoomsSurgeryEngine(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()
        # Basic state with default setup
        self.state = GameState()

    def test_surgery_heals_and_clears(self):
        """Test that SURGERY room heals 1 HP and clears 1 serious wound."""
        # Set up state with player in room D (SURGERY), health=4, serious_wounds=1
        state = self.state.next(
            player_room="D",  # D is SURGERY
            health=4,
            serious_wounds=1,
        )
        
        # Verify room type is SURGERY
        self.assertEqual(state.board.room_types.get("D"), "SURGERY")
        
        # USE_ROOM action should be legal
        actions = self.rules.legal_actions(state)
        self.assertTrue(any(a.type == ActionType.USE_ROOM for a in actions))
        
        # Apply USE_ROOM action
        action = Action(ActionType.USE_ROOM)
        next_state = self.rules.apply(state, action)
        
        # Check that health increased to 5
        self.assertEqual(next_state.health, 5)
        
        # Check that serious wound was cleared
        self.assertEqual(next_state.serious_wounds, 0)
        
        # Check that it counted as an action
        self.assertEqual(next_state.actions_in_turn, 1)

    def test_engine_arms_and_counts_down(self):
        """Test that ENGINE room arms self-destruct and timer counts down in CLEANUP."""
        # Set up state with player in room E (ENGINE)
        state = self.state.next(
            player_room="E",  # E is ENGINE
        )
        
        # Verify room type is ENGINE
        self.assertEqual(state.board.room_types.get("E"), "ENGINE")
        
        # USE_ROOM action should be legal
        actions = self.rules.legal_actions(state)
        self.assertTrue(any(a.type == ActionType.USE_ROOM for a in actions))
        
        # Apply USE_ROOM action to arm self-destruct
        action = Action(ActionType.USE_ROOM)
        next_state = self.rules.apply(state, action)
        
        # Check that self-destruct is armed
        self.assertTrue(next_state.self_destruct_armed)
        
        # Check that timer is set to 3
        self.assertEqual(next_state.destruction_timer, 3)
        
        # Check that it counted as an action
        self.assertEqual(next_state.actions_in_turn, 1)
        
        # Finish the current turn with PASS so actions_in_turn resets
        action = Action(ActionType.PASS)
        pass_state = self.rules.apply(next_state, action)
        self.assertEqual(pass_state.phase, Phase.PLAYER)  # still player phase
        self.assertEqual(pass_state.actions_in_turn, 0)

        # Now end player phase
        action = Action(ActionType.END_PLAYER_PHASE)
        enemy_state = self.rules.apply(pass_state, action)
        self.assertEqual(enemy_state.phase, Phase.ENEMY)
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        event_state = self.rules.apply(enemy_state, action)
        self.assertEqual(event_state.phase, Phase.EVENT)
        
        # Advance to CLEANUP phase
        action = Action(ActionType.NEXT_PHASE)
        cleanup_state = self.rules.apply(event_state, action)
        self.assertEqual(cleanup_state.phase, Phase.CLEANUP)
        
        # Check that timer decremented to 2
        self.assertEqual(cleanup_state.destruction_timer, 2)
        
        # Self-destruct should still be armed
        self.assertTrue(cleanup_state.self_destruct_armed)


if __name__ == "__main__":
    unittest.main()
