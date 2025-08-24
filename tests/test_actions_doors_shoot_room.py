import unittest
from src.n_r_ai.core.game_state import GameState, Phase
from src.n_r_ai.core.actions import Action, ActionType
from src.n_r_ai.core.rules import Rules

class TestActionsDoorShootRoom(unittest.TestCase):
    def setUp(self):
        self.rules = Rules()
        # Basic board with A-B-C, door between A-B initially closed
        self.initial_state = GameState(
            player_room="A",
            doors={("A", "B")},  # Door between A and B is closed
            phase=Phase.PLAYER
        )

    def test_open_door_enables_movement(self):
        """Test that OPEN_DOOR action enables movement through previously closed edge."""
        state = self.initial_state
        
        # Verify door is closed and movement is not possible
        legal_actions = self.rules.legal_actions(state)
        move_actions = [a for a in legal_actions if a.type == ActionType.MOVE and a.params.get("to") == "B"]
        self.assertEqual(len(move_actions), 0, "Should not be able to move to B when door is closed")
        
        # Verify OPEN_DOOR action is available
        open_door_actions = [a for a in legal_actions if a.type == ActionType.OPEN_DOOR and a.params.get("to") == "B"]
        self.assertEqual(len(open_door_actions), 1, "Should have OPEN_DOOR action available")
        
        # Open the door
        open_door_action = open_door_actions[0]
        state_after_open = self.rules.apply(state, open_door_action)
        
        # Verify door is now open
        self.assertNotIn(("A", "B"), state_after_open.doors, "Door should be open after OPEN_DOOR action")
        
        # Verify movement is now possible
        legal_actions_after_open = self.rules.legal_actions(state_after_open)
        move_actions_after_open = [a for a in legal_actions_after_open if a.type == ActionType.MOVE and a.params.get("to") == "B"]
        self.assertEqual(len(move_actions_after_open), 1, "Should be able to move to B after door is opened")

    def test_close_door_blocks_movement(self):
        """Test that CLOSE_DOOR action blocks movement through previously open edge."""
        # Start with door open
        state = self.initial_state.next(doors=set())
        
        # Verify movement is possible
        legal_actions = self.rules.legal_actions(state)
        move_actions = [a for a in legal_actions if a.type == ActionType.MOVE and a.params.get("to") == "B"]
        self.assertEqual(len(move_actions), 1, "Should be able to move to B when door is open")
        
        # Verify CLOSE_DOOR action is available
        close_door_actions = [a for a in legal_actions if a.type == ActionType.CLOSE_DOOR and a.params.get("to") == "B"]
        self.assertEqual(len(close_door_actions), 1, "Should have CLOSE_DOOR action available")
        
        # Close the door
        close_door_action = close_door_actions[0]
        state_after_close = self.rules.apply(state, close_door_action)
        
        # Verify door is now closed
        self.assertIn(("A", "B"), state_after_close.doors, "Door should be closed after CLOSE_DOOR action")
        
        # Verify movement is now blocked
        legal_actions_after_close = self.rules.legal_actions(state_after_close)
        move_actions_after_close = [a for a in legal_actions_after_close if a.type == ActionType.MOVE and a.params.get("to") == "B"]
        self.assertEqual(len(move_actions_after_close), 0, "Should not be able to move to B after door is closed")

    def test_shoot_reduces_hp_and_removes_intruder(self):
        """Test that SHOOT action reduces intruder HP and removes it when HP <= 0."""
        # Create state with intruder in player's room with HP=2
        state = self.initial_state.next(intruders={"A": 2})
        
        # Verify SHOOT action is available
        legal_actions = self.rules.legal_actions(state)
        shoot_actions = [a for a in legal_actions if a.type == ActionType.SHOOT]
        self.assertEqual(len(shoot_actions), 1, "Should have SHOOT action available when intruder is present")
        
        # Shoot once
        shoot_action = shoot_actions[0]
        state_after_shoot = self.rules.apply(state, shoot_action)
        
        # Verify HP reduced to 1
        self.assertEqual(state_after_shoot.intruders.get("A", 0), 1, "Intruder HP should be reduced to 1 after first SHOOT")
        
        # Shoot again
        state_after_second_shoot = self.rules.apply(state_after_shoot, shoot_action)
        
        # Verify intruder is removed
        self.assertNotIn("A", state_after_second_shoot.intruders, "Intruder should be removed after second SHOOT")

    def test_use_room_toggles_life_support(self):
        """Test that USE_ROOM action in room B toggles life_support_active."""
        # Create state with player in room B and life support active
        state = self.initial_state.next(player_room="B", life_support_active=True)
        
        # Verify USE_ROOM action is available
        legal_actions = self.rules.legal_actions(state)
        use_room_actions = [a for a in legal_actions if a.type == ActionType.USE_ROOM]
        self.assertEqual(len(use_room_actions), 1, "Should have USE_ROOM action available in room B")
        
        # Use room to toggle life support off
        use_room_action = use_room_actions[0]
        state_after_use = self.rules.apply(state, use_room_action)
        
        # Verify life support is now off
        self.assertFalse(state_after_use.life_support_active, "Life support should be off after first USE_ROOM")
        
        # Use room again to toggle life support back on
        state_after_second_use = self.rules.apply(state_after_use, use_room_action)
        
        # Verify life support is now on again
        self.assertTrue(state_after_second_use.life_support_active, "Life support should be on after second USE_ROOM")

    # ------------------------------------------------------------------ #
    # New tests for melee combat and Armory reload                       #
    # ------------------------------------------------------------------ #

    def test_melee_damages_both(self):
        """MELEE should hurt intruder and player each time it is used."""
        state = self.initial_state.next(intruders={"A": 2}, health=5)

        # MELEE must be available (ammo irrelevant)
        legal = self.rules.legal_actions(state)
        melee_actions = [a for a in legal if a.type == ActionType.MELEE]
        self.assertEqual(len(melee_actions), 1, "MELEE action should be legal when intruder present")

        # First melee → intruder HP 2→1, player 5→4
        s1 = self.rules.apply(state, melee_actions[0])
        self.assertEqual(s1.intruders.get("A", 0), 1, "Intruder HP should drop by 1")
        self.assertEqual(s1.health, 4, "Player health should drop by 1 after melee")

        # Second melee → intruder removed, player 4→3
        s2 = self.rules.apply(s1, melee_actions[0])
        self.assertNotIn("A", s2.intruders, "Intruder should be eliminated after second melee")
        self.assertEqual(s2.health, 3, "Player health should drop again after second melee")

    def test_armory_reload_restores_ammo(self):
        """Using the Armory (room C) should refill ammo to ammo_max."""
        # Move player to C (Armory) with zero ammo; ensure doors are open
        state = self.initial_state.next(player_room="C", doors=set(), ammo=0)

        # Armory USE_ROOM action must be legal
        legal = self.rules.legal_actions(state)
        reload_actions = [a for a in legal if a.type == ActionType.USE_ROOM]
        self.assertEqual(len(reload_actions), 1, "USE_ROOM (reload) should be legal in Armory")

        # Apply reload
        s1 = self.rules.apply(state, reload_actions[0])
        self.assertEqual(
            s1.ammo, s1.ammo_max,
            "Ammo should be fully restored to ammo_max after reload in Armory"
        )

if __name__ == "__main__":
    unittest.main()
