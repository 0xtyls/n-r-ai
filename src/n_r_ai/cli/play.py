from __future__ import annotations
from ..engine.environment import Environment
from ..core.actions import Action, ActionType


def main() -> None:
    env = Environment()
    state = env.reset()
    for _ in range(3):
        state, _, done, _ = env.step(Action(ActionType.NOOP))
        if done:
            break

if __name__ == "__main__":
    main()
