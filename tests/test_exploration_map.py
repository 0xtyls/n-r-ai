import unittest

from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules

class TestExplorationMap(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()
        # Start with only the starting room discovered to exercise exploration
        self.base = GameState(
            player_room="A",
            phase=Phase.PLAYER,
            discovered_rooms={"A"},
            # small exploration deck we can control; top card index 0
            exploration_deck_cards=[
                "ENTRANCE_NOISE_ROOM",
                "ENTRANCE_CLOSE_DOORS",
                "ENTRANCE_NOISE_CORRIDOR",
            ],
            # ensure no doors block A->B
            doors=set(),
        )

    def test_exploration_noise_room_and_discover(self):
        s0 = self.base
        # Move to B; B is undiscovered, first card is ENTRANCE_NOISE_ROOM
        move = [a for a in self.rules.legal_actions(s0) if a.type == ActionType.MOVE and a.params.get("to") == "B"][0]
        s1 = self.rules.apply(s0, move)

        # B should now be discovered
        self.assertIn("B", s1.discovered_rooms)
        # Room noise placed in B; corridor noise for A-B should not be incremented by standard move
        self.assertEqual(s1.room_noise.get("B", 0), 1)
        self.assertEqual(s1.noise.get(tuple(sorted(("A","B"))), 0), 0)
        # Exploration deck consumed 1 card
        self.assertEqual(len(s1.exploration_deck_cards), 2)

    def test_exploration_cautious_places_secure(self):
        s0 = self.base
        # Use MOVE_CAUTIOUS into B; should place secure token on A-B edge during exploration
        move_c = [a for a in self.rules.legal_actions(s0) if a.type == ActionType.MOVE_CAUTIOUS and a.params.get("to") == "B"][0]
        s1 = self.rules.apply(s0, move_c)
        edge = tuple(sorted(("A","B")))
        self.assertIn(edge, s1.secure_tokens)

    def test_exploration_close_doors_effect(self):
        # Consume first card to reach CLOSE_DOORS as next
        s0 = self.base
        move1 = [a for a in self.rules.legal_actions(s0) if a.type == ActionType.MOVE and a.params.get("to") == "B"][0]
        s1 = self.rules.apply(s0, move1)
        # Now back to A manually to test second card
        s1 = s1.next(player_room="A")

        # Ensure B is undiscovered again for this test path
        s1 = s1.next(discovered_rooms={"A"})

        # Next card is ENTRANCE_CLOSE_DOORS
        move2 = [a for a in self.rules.legal_actions(s1) if a.type == ActionType.MOVE and a.params.get("to") == "B"][0]
        s2 = self.rules.apply(s1, move2)

        # All doors around B should be closed
        for nb in s2.board.neighbors("B"):
            edge = tuple(sorted(("B", nb)))
            self.assertIn(edge, s2.doors)

if __name__ == "__main__":
    unittest.main()
