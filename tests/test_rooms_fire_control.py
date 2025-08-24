import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules

class TestRoomFireControl(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()

    def test_fire_control_extinguishes_fire(self):
        # Player in A (Fire Control), room A is on fire
        s = GameState(player_room="A", fires={"A"}, phase=Phase.PLAYER)
        # USE_ROOM should be available
        legal = self.rules.legal_actions(s)
        use_actions = [a for a in legal if a.type == ActionType.USE_ROOM]
        self.assertEqual(len(use_actions), 1)
        
        # Use Fire Control: should remove fire
        s1 = self.rules.apply(s, use_actions[0])
        self.assertNotIn("A", s1.fires)
        self.assertEqual(s1.actions_in_turn, 1)

    def test_fire_control_no_fire_still_consumes_action(self):
        # Player in A (Fire Control), no fire present
        s = GameState(player_room="A", fires=set(), phase=Phase.PLAYER)
        legal = self.rules.legal_actions(s)
        use_actions = [a for a in legal if a.type == ActionType.USE_ROOM]
        self.assertEqual(len(use_actions), 1)
        
        s1 = self.rules.apply(s, use_actions[0])
        # No fires to remove; should still count as action
        self.assertEqual(s1.fires, set())
        self.assertEqual(s1.actions_in_turn, 1)

if __name__ == "__main__":
    unittest.main()
