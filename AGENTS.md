# Agents Guide

This document explains how agents interact with the game core, server, and UI in this repository.

---

## TL;DR for implementers
- **Implement**: an agent exposes `act(state: GameState) -> Action`.
- **Use**: current rules expose legal actions via `Rules.legal_actions(state)`.
- **Run**: backend FastAPI in `src/n_r_ai/server`, web UI in `web/`.
- **LLM**: OpenAI-compatible client; configure via env vars.

---

## Modules Overview
- **core/**
  - `game_state.py`: immutable `GameState` with `Phase` and `next()` helper.
  - `actions.py`: `ActionType` and `Action` (currently NOOP only; will expand).
  - `rules.py`: placeholder rules; returns legal actions, applies action to state.
  - `board.py`, `entities.py`, `rng.py`: stubs to evolve with the game model.
- **engine/**
  - `environment.py`: `Environment` wrapper with `reset()` and `step()`.
  - `simulator.py`: `step(state, action, rules)` thin adapter.
  - `validator.py`: stub for state validation.
- **ai/**
  - `agents/base.py`: `Agent` protocol with `act(state) -> Action`.
  - `agents/random_agent.py`: picks uniformly from legal actions.
  - `agents/llm_agent.py`: LLM-driven agent that role-plays a persona.
  - `mcts/`: minimal MCTS scaffold (`node.py`, `mcts.py`).
  - `policy.py`: example uniform policy.
- **server/**
  - `app.py`: FastAPI app with REST endpoints and CORS for web UI.
  - `llm.py`: OpenAI-compatible helper used by server and `LLMAgent`.
- **web/**
  - Vite + React (TS). Shows state, lists actions, lets LLM pick an action.

---

## Agent Protocol
- **Signature**: `act(state: GameState) -> Action`.
- Agents **MUST** return only legal actions. Typical pattern:
  ```python
  actions = rules.legal_actions(state)
  # choose one of actions
  return actions[0]
  ```
- **Determinism**: not required. Random/LLM agents may vary per call.

---

## Available Agents
| Agent | Behaviour |
|-------|-----------|
| `RandomAgent` | Uniform random legal action |
| **MCTS** (skeleton) | `search(state, iters)`; placeholder logic |
| `LLMAgent` | Summarises state & actions, prompts an LLM, persona-driven |

---

## LLM Integration
- Uses **OpenAI-compatible** client via the `openai` package.
- **Environment vars** (example for DeepSeek):
  ```
  OPENAI_API_KEY=sk-...
  LLM_BASE_URL=https://api.deepseek.com/v1
  LLM_MODEL=deepseek-chat
  LLM_TEMPERATURE=0.7
  ```
- Helper: `src/n_r_ai/server/llm.py`
  - System prompt asks to role-play and return **strict JSON** only.
  - **Input**: `state_summary: str`, `actions: list[{type, params}]`, optional persona.
  - **Output JSON**: `{ "pick": <int index>, "rationale": <string> }`.
- **Server endpoint**: `POST /api/llm_act`
  - **Request**: `{ persona?: string, temperature?: number }`
  - **Response**: `{ chosen: {type, params}, rationale: string, state: {turn, phase, seed} }`

---

## Backend API (for UI or external orchestrators)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/state` | Current `GameState` summary |
| GET | `/api/actions` | List of legal actions |
| POST | `/api/step` | Apply specific action |
| POST | `/api/llm_act` | Ask LLM to choose and apply an action |

---

## Running Locally
1. **Backend**
   ```bash
   pip install -e .
   python -m n_r_ai.server  # http://127.0.0.1:8000
   ```
2. **Frontend**
   ```bash
   cd web
   npm install
   npm run dev  # http://127.0.0.1:5173
   ```
   Set `VITE_API_URL` if backend runs elsewhere.

---

## Writing a New Agent
1. Create `src/n_r_ai/ai/agents/your_agent.py`.
2. Implement `act(state: GameState) -> Action` (use `Rules.legal_actions`).
3. Optional: add a server endpoint or CLI wrapper if you want remote/UI access.

Example template:
```python
from __future__ import annotations
from ...core.game_state import GameState
from ...core.actions import Action
from ...core.rules import Rules

class YourAgent:
    def __init__(self, rules: Rules | None = None) -> None:
        self.rules = rules or Rules()

    def act(self, state: GameState) -> Action:
        actions = self.rules.legal_actions(state)
        # choose an action from actions
        return actions[0]
```

---

## Multi-Agent Matches
- **In-process**: instantiate multiple agents (e.g., several `LLMAgent` with different personas) and alternate calls to `act()` + `Environment.step()`.
- **Over HTTP**: orchestrate turns by calling `/api/state`, `/api/actions`, and `/api/llm_act` with different personas per player.

---

## Notes
- Current rules expose only `NOOP`; expand actions/state to unlock richer play.
- Keep prompts concise; prefer structured inputs and JSON outputs for reliability.
