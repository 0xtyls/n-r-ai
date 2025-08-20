from __future__ import annotations
from ..engine.environment import Environment
from ..ai.agents.random_agent import RandomAgent
from ..core.actions import ActionType, Action


def run(steps: int = 5) -> None:
    env = Environment()
    agent = RandomAgent()
    state = env.reset()
    for _ in range(steps):
        action = agent.act(state)
        state, _, done, _ = env.step(action)
        if done:
            break

if __name__ == "__main__":
    run()
