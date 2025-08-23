import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules


class TestEventBagSkeleton(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()
        # Basic state with player in room A
        self.state = GameState(
            player_room="A",
            phase=Phase.ENEMY,  # Start in ENEMY phase to easily transition to EVENT
        )

    def test_event_noise_room(self):
        """Test that NOISE_ROOM event adds noise to player's room."""
        # Set up state with a NOISE_ROOM card at the top of the deck
        state = self.state.next(
            event_deck_cards=["NOISE_ROOM"],
            event_deck=1,
        )
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        next_state = self.rules.apply(state, action)
        
        # Check that we're in EVENT phase
        self.assertEqual(next_state.phase, Phase.EVENT)
        
        # Check that room noise was added to player's room
        self.assertEqual(next_state.room_noise.get("A", 0), 1)
        
        # Check that event deck is now empty
        self.assertEqual(next_state.event_deck, 0)
        self.assertEqual(len(next_state.event_deck_cards), 0)

    def test_event_noise_corridor(self):
        """Test that NOISE_CORRIDOR event adds noise to a corridor."""
        # Set up state with a NOISE_CORRIDOR card at the top of the deck
        state = self.state.next(
            event_deck_cards=["NOISE_CORRIDOR"],
            event_deck=1,
        )
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        next_state = self.rules.apply(state, action)
        
        # Check that corridor noise was added
        # The deterministic implementation should add noise to the A-B edge
        edge = tuple(sorted(("A", "B")))
        self.assertGreater(next_state.noise.get(edge, 0), 0)
        
        # Check that event deck is now empty
        self.assertEqual(next_state.event_deck, 0)
        self.assertEqual(len(next_state.event_deck_cards), 0)

    def test_event_bag_dev(self):
        """Test that BAG_DEV event increments bag_dev_count."""
        # Set up state with a BAG_DEV card at the top of the deck
        initial_bag_dev = 3
        state = self.state.next(
            event_deck_cards=["BAG_DEV"],
            event_deck=1,
            bag_dev_count=initial_bag_dev,
        )
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        next_state = self.rules.apply(state, action)
        
        # Check that bag_dev_count was incremented
        self.assertEqual(next_state.bag_dev_count, initial_bag_dev + 1)
        
        # Check that event deck is now empty
        self.assertEqual(next_state.event_deck, 0)
        self.assertEqual(len(next_state.event_deck_cards), 0)

    def test_event_spawn_from_bag(self):
        """Test that SPAWN_FROM_BAG event spawns an intruder in player's room."""
        # Set up state with a SPAWN_FROM_BAG card and ADULT token in bag
        state = self.state.next(
            event_deck_cards=["SPAWN_FROM_BAG"],
            event_deck=1,
            bag={"ADULT": 1, "LARVA": 2},  # ADULT should be drawn first (alphabetical)
        )
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        next_state = self.rules.apply(state, action)
        
        # Check that an intruder was spawned in player's room
        self.assertIn("A", next_state.intruders)
        self.assertEqual(next_state.intruders["A"], 1)  # HP should be 1
        
        # Check that ADULT token was removed from bag
        self.assertNotIn("ADULT", next_state.bag)
        self.assertEqual(next_state.bag["LARVA"], 2)  # LARVA tokens should remain
        
        # Check that event deck is now empty
        self.assertEqual(next_state.event_deck, 0)
        self.assertEqual(len(next_state.event_deck_cards), 0)

    def test_multiple_event_cards(self):
        """Test processing multiple event cards in sequence."""
        # Set up state with multiple event cards
        state = self.state.next(
            event_deck_cards=["NOISE_ROOM", "BAG_DEV", "SPAWN_FROM_BAG"],
            event_deck=3,
            bag={"ADULT": 1, "LARVA": 1},
        )
        
        # Advance to EVENT phase - should process NOISE_ROOM
        action = Action(ActionType.NEXT_PHASE)
        state1 = self.rules.apply(state, action)
        
        # Check NOISE_ROOM effects
        self.assertEqual(state1.room_noise.get("A", 0), 1)
        self.assertEqual(state1.event_deck, 2)
        self.assertEqual(len(state1.event_deck_cards), 2)
        
        # Advance to CLEANUP phase
        action = Action(ActionType.NEXT_PHASE)
        state2 = self.rules.apply(state1, action)
        self.assertEqual(state2.phase, Phase.CLEANUP)
        
        # Advance to PLAYER phase
        action = Action(ActionType.NEXT_PHASE)
        state3 = self.rules.apply(state2, action)
        self.assertEqual(state3.phase, Phase.PLAYER)
        
        # Advance to ENEMY phase
        action = Action(ActionType.END_PLAYER_PHASE)
        state4 = self.rules.apply(state3, action)
        self.assertEqual(state4.phase, Phase.ENEMY)
        
        # Advance to EVENT phase again - should process BAG_DEV
        action = Action(ActionType.NEXT_PHASE)
        state5 = self.rules.apply(state4, action)
        
        # Check BAG_DEV effects
        self.assertEqual(state5.bag_dev_count, 1)
        self.assertEqual(state5.event_deck, 1)
        self.assertEqual(len(state5.event_deck_cards), 1)
        
        # Complete another round to get to the next EVENT phase
        action = Action(ActionType.NEXT_PHASE)  # CLEANUP
        state6 = self.rules.apply(state5, action)
        action = Action(ActionType.NEXT_PHASE)  # PLAYER
        state7 = self.rules.apply(state6, action)
        action = Action(ActionType.END_PLAYER_PHASE)  # ENEMY
        state8 = self.rules.apply(state7, action)
        action = Action(ActionType.NEXT_PHASE)  # EVENT - should process SPAWN_FROM_BAG
        state9 = self.rules.apply(state8, action)
        
        # Check SPAWN_FROM_BAG effects
        self.assertIn("A", state9.intruders)
        self.assertEqual(state9.event_deck, 0)
        self.assertEqual(len(state9.event_deck_cards), 0)
        self.assertNotIn("ADULT", state9.bag)

    def test_fallback_when_no_cards(self):
        """Test fallback behavior when event deck is empty."""
        # Set up state with empty event deck but event_deck counter > 0
        state = self.state.next(
            event_deck_cards=[],
            event_deck=5,  # Intentionally mismatched to test fallback
        )
        
        # Advance to EVENT phase
        action = Action(ActionType.NEXT_PHASE)
        next_state = self.rules.apply(state, action)
        
        # Check that event_deck counter was decremented
        self.assertEqual(next_state.event_deck, 4)
        
        # Check that fallback noise was added (either room or corridor)
        has_noise = False
        if next_state.room_noise.get("A", 0) > 0:
            has_noise = True
        else:
            for edge, count in next_state.noise.items():
                if count > 0:
                    has_noise = True
                    break
        
        self.assertTrue(has_noise, "No noise was added during fallback")


if __name__ == "__main__":
    unittest.main()
