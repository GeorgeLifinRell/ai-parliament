# 🏛️ AI Parliament — Constrained Multi-Agent Governance System

> A research-grade multi-agent architecture where **institutions constrain intelligence**, not the other way around.

This project implements a fully working **AI Parliament**:

- Multiple LLM-powered faction agents (Cerebras/Gemini)
- LLM-backed Speaker for strategic procedural decisions
- Multi-round debate system with targeted persuasion
- Immutable constitutional data models
- Dynamic veto power assignment
- Schema-validated structured outputs
- Colorful terminal interface
- Robust failure handling (agents abstain instead of crashing)

This is **not** a chatbot swarm.
It is a **governance system encoded in software**.

---

## 🎯 Project Goal

To build an AI system that:

- Produces decisions through **structured disagreement**
- Enforces **procedure and legitimacy**
- Prevents silent corruption (immutability everywhere)
- Allows intelligence (LLMs) **only within strict constraints**
- Produces outcomes that are:

  - Explainable
  - Auditable
  - Reproducible
  - Political rather than optimized

---

## 🧠 Architecture Overview

```
Bill / DebateArgument / Amendment / Vote (immutable, validated)
        ↓
     Speaker (LLM-backed procedural authority)
        ↓
  Agents (LLM-backed, constrained actors)
        ↓
 Voting Engine (mechanical aggregation + veto)
        ↓
     Decision (immutable record of outcome)
```

Key principle:

> **Institutions control agents. Agents never control institutions.**

---

## ✅ What Is Implemented

### 1. Constitutional Core (Pydantic v2)

All immutable, strictly validated:

- `Bill`
- `DebateArgument`
- `Amendment`
- `Vote`
- `Decision`

These enforce:

- No mutation of history
- No malformed state
- No empty or invalid inputs
- No silent corruption

---

### 2. Procedure Layer

#### Speaker (LLM-Backed)

Enforces phases:

- INTRODUCTION
- FACTION_STATEMENTS
- DEBATE (multi-round persuasion)
- AMENDMENTS
- VOTING
- DECISION

Strategic decisions (LLM-powered):

- Determines debate speaking order
- Assigns veto power to fit factions
- Graceful degradation on LLM failure

Procedural enforcement (mechanical):

- No phase skipping
- Can force vote
- Validates all actions

Speaker = **authority with strategic intelligence, zero policy opinion**

---

### 3. Voting Engine

- Weight-based aggregation
- One vote per faction
- Validates bill/version correctness
- Ties fail
- Speaker-assigned veto factions (dynamic per bill)
- Produces immutable `Decision`

Voting is **blind and mechanical**.

---

### 4. Configuration (YAML Driven Governance)

Governance is configurable without code changes:

- `factions.yaml` → ideology (goals, priorities, red lines)
- `procedure.yaml` → phases, limits
- `voting.yaml` → weights, veto factions

This allows changing political structure without touching logic.

---

### 5. Agents (LLM-powered)

Each faction is an LLM-backed agent:

- Efficiency
- Safety
- Equity
- Innovation
- Compliance

Agents:

- Generate initial position statements
- Debate and persuade other factions (can target specific factions)
- Propose amendments
- Cast final votes
- Must output structured JSON
- Are schema-validated
- Cannot mutate state
- Cannot change procedure
- Cannot see other agents' private reasoning
- Abstain if LLM fails

LLMs are treated as **untrusted witnesses**.

---

### 6. LLM Layer

Robust LLM client with multiple providers:

- Default: **Cerebras** (`llama-3.3-70b`)
- Alternative: **Google Gemini** (`gemini-2.0-flash`)
- Forces JSON output
- Extracts JSON even if wrapped
- Retries on invalid responses
- Hard fails if corruption persists
- Agents gracefully degrade (abstain instead of crash)

---

### 7. Working End-to-End Simulation

You can run a complete session:

- Example bill created
- Speaker assigns veto power strategically
- All agents generate statements
- Multi-round debate (agents persuade each other)
- Amendments proposed
- Votes cast
- Voting engine evaluates
- Final decision printed (with colorful terminal output)

You get real emergent behavior like:

- Safety faction rejecting risky proposals
- Compliance vetoing policy violations
- Innovation supporting risky upside
- Equity raising fairness concerns
- Efficiency proposing scope reductions
- Factions strategically targeting arguments in debate

This produces **political outcomes, not consensus answers**.

---

## ▶️ How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Required packages:

- pydantic>=2
- pyyaml
- langchain-cerebras (default LLM provider)
- google-generativeai (alternative provider)
- pytest

---

### 2. Set API keys

```bash
export CEREBRAS_API_KEY="your_cerebras_key"  # Default provider
# OR
export GEMINI_API_KEY="your_gemini_key"  # Alternative provider
```

---

### 3. Run simulation

```bash
python main.py
```

You'll see colorful terminal output showing:

```
🏛️  AI PARLIAMENT SIMULATION

⚖️  SPEAKER AUTHORITY (LLM-Backed)
[Speaker] Veto power reasoning: ...

💬 FACTION STATEMENTS
[Efficiency] ...
[Safety] ...

🗣️  DEBATE PHASE
>>> Debate Round 1 <<<
[Safety] → [Innovation, Efficiency]
  We must ensure robust safety measures...

✏️  AMENDMENTS
[Efficiency] proposes: ...

🗳️  VOTING
[Safety] votes: REJECT
[Innovation] votes: APPROVE

⚖️  FINAL DECISION
Bill Status: ✗ REJECTED
Vetoed By: Safety, Compliance
```

---

## 🧪 Robustness Features

- If LLM returns malformed JSON → retried
- If LLM still fails → agent/speaker abstains or uses defaults
- No agent failure can crash the parliament
- All decisions remain valid and auditable
- Strict schema enforcement everywhere
- Colorful terminal output for easy monitoring

This mirrors real institutions:

> If a representative fails to speak, they abstain.
> The institution continues.

---

## 🧱 Why This Is Different from Typical Agent Projects

| Typical agent systems | AI Parliament             |
| --------------------- | ------------------------- |
| Agents control flow   | Institutions control flow |
| Mutable state         | Immutable history         |
| Free-form text        | Schema validated outputs  |
| Agents cooperate      | Agents conflict           |
| Consensus-seeking     | Legitimacy-seeking        |
| Optimized answers     | Political outcomes        |
| Fragile pipelines     | Graceful degradation      |

This is closer to:

- governance systems
- distributed institutions
- constitutional AI architectures
  than to chatbots.

---

## 🚀 What We Achieved

You now have:

- A functioning multi-agent LLM system
- With real ideological disagreement
- With strategic procedural authority (LLM-backed Speaker)
- With multi-round persuasive debates
- With dynamic veto power assignment
- With enforced legitimacy
- With procedural constraints
- With robust LLM integration
- With explainable, colorful outputs

This is research-grade architecture.

---

## 🛣️ Possible Next Directions

Future extensions:

- Applying accepted amendments → new bill versions
- Precedent and memory
- Persistent session history
- Web UI dashboard
- Running large-scale simulations (100s of parliaments)
- Adversarial testing (malicious proposals)

---

## ⚠️ Design Philosophy

> Intelligence must never outrun legitimacy.

LLMs are powerful but unreliable.
This system treats them as **participants under law**, not as controllers.

That's the core idea of this project.

---
