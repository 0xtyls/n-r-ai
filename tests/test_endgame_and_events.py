import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules

class TestEndgameAndEvents(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()

    def test_escape_win_in_engine(self):
        state = GameState(player_room="E", phase=Phase.PLAYER)
        actions = self.rules.legal_actions(state)
        self.assertIn(ActionType.ESCAPE, [a.type for a in actions])
        next_state = self.rules.apply(state, Action(ActionType.ESCAPE))
        self.assertTrue(next_state.game_over)
        self.assertTrue(next_state.win)

    def test_oxygen_leak_and_fire_room(self):
        # Start in ENEMY to advance to EVENT quickly
        state = GameState(player_room="B", phase=Phase.ENEMY)
        # Two events in sequence: oxygen leak then fire in room
        state = state.next(event_deck_cards=["OXYGEN_LEAK", "FIRE_ROOM"], event_deck=2)

        # ENEMY -> EVENT (process OXYGEN_LEAK)
        s1 = self.rules.apply(state, Action(ActionType.NEXT_PHASE))
        self.assertEqual(s1.phase, Phase.EVENT)
        self.assertFalse(s1.life_support_active)
        self.assertEqual(s1.event_deck, 1)

        # EVENT -> CLEANUP -> PLAYER -> ENEMY
        s2 = self.rules.apply(s1, Action(ActionType.NEXT_PHASE))  # CLEANUP
        s3 = self.rules.apply(s2, Action(ActionType.NEXT_PHASE))  # PLAYER
        s4 = self.rules.apply(s3, Action(ActionType.END_PLAYER_PHASE))  # ENEMY
        # ENEMY -> EVENT (process FIRE_ROOM)
        s5 = self.rules.apply(s4, Action(ActionType.NEXT_PHASE))
        self.assertIn("B", s5.fires)
        self.assertEqual(s5.event_deck, 0)

    def test_self_destruct_loss(self):
        # Move to ENGINE and arm self-destruct, then run countdown to loss
        s = GameState(player_room="E", phase=Phase.PLAYER)
        # Arm self destruct via USE_ROOM
        s1 = self.rules.apply(s, Action(ActionType.USE_ROOM))
        self.assertTrue(s1.self_destruct_armed)
        self.assertEqual(s1.destruction_timer, 3)

        # End player phase and cycle phases 3 times to reach timer 0
        # Insert PASS before END_PLAYER_PHASE to reset actions_in_turn
        s1p = self.rules.apply(s1, Action(ActionType.PASS))
        s2 = self.rules.apply(s1p, Action(ActionType.END_PLAYER_PHASE))  # ENEMY
        s3 = self.rules.apply(s2, Action(ActionType.NEXT_PHASE))         # EVENT
        s4 = self.rules.apply(s3, Action(ActionType.NEXT_PHASE))         # CLEANUP -> timer 2

        # Next PLAYER round -------------------------------------------------
        s5p = self.rules.apply(s4, Action(ActionType.NEXT_PHASE))         # PLAYER
        s6 = self.rules.apply(s5p, Action(ActionType.PASS))
        s7 = self.rules.apply(s6, Action(ActionType.END_PLAYER_PHASE))    # ENEMY
        s8 = self.rules.apply(s7, Action(ActionType.NEXT_PHASE))          # EVENT
        s9 = self.rules.apply(s8, Action(ActionType.NEXT_PHASE))          # CLEANUP -> timer 1

        # Final PLAYER round ------------------------------------------------
        s10p = self.rules.apply(s9, Action(ActionType.NEXT_PHASE))        # PLAYER
        s11 = self.rules.apply(s10p, Action(ActionType.PASS))
        s12 = self.rules.apply(s11, Action(ActionType.END_PLAYER_PHASE))  # ENEMY
        s13 = self.rules.apply(s12, Action(ActionType.NEXT_PHASE))        # EVENT
        s14 = self.rules.apply(s13, Action(ActionType.NEXT_PHASE))        # CLEANUP -> timer 0 -> game over (loss)

        self.assertTrue(s14.game_over)
        self.assertFalse(s14.win)

if __name__ == "__main__":
    unittest.main()
