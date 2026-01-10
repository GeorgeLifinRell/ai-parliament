# 🏛️ AI Parliament — Constrained Multi-Agent Governance System

> A research-grade multi-agent architecture where **institutions constrain intelligence**, not the other way around.

This project implements a fully working **AI Parliament**:

- Multiple LLM-powered faction agents (Gemini)
- Immutable constitutional data models
- A procedural Speaker enforcing phases
- A deterministic Voting Engine with vetoes
- Schema-validated structured outputs
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
Bill / Amendment / Vote (immutable, validated)
        ↓
     Speaker (procedure enforcement)
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

#### Speaker

- Enforces phases:

  - INTRODUCTION
  - FACTION_STATEMENTS
  - AMENDMENTS
  - VOTING
  - DECISION

- No phase skipping
- Can force vote
- No content reasoning
- No influence on outcomes

Speaker = **authority without intelligence**

---

### 3. Voting Engine

- Weight-based aggregation
- One vote per faction
- Validates bill/version correctness
- Ties fail
- Supports veto factions
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

### 5. Agents (Gemini LLM-powered)

Each faction is an LLM-backed agent:

- Efficiency
- Safety
- Equity
- Innovation
- Compliance

Agents:

- Must output structured JSON
- Are schema-validated
- Cannot mutate state
- Cannot change procedure
- Cannot see other agents' private reasoning
- Abstain if LLM fails

LLMs are treated as **untrusted witnesses**.

---

### 6. LLM Layer (Gemini via google-generativeai)

Robust LLM client:

- Forces JSON output
- Extracts JSON even if wrapped
- Retries on invalid responses
- Hard fails if corruption persists
- Agents gracefully degrade (abstain instead of crash)

Working model:

- `gemini-2.5-flash`

---

### 7. Working End-to-End Simulation

You can run a complete session:

- Example bill created
- All agents generate statements
- Amendments proposed
- Votes cast
- Voting engine evaluates
- Final decision printed

You get real emergent behavior like:

- Safety faction rejecting risky proposals
- Compliance vetoing policy violations
- Innovation supporting risky upside
- Equity raising fairness concerns
- Efficiency proposing scope reductions

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
- google-generativeai
- pytest

---

### 2. Set Gemini API key

```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

### 3. Run simulation

```bash
python main.py
```

You should see output like:

```
--- FACTION STATEMENTS ---
[Safety] ...
[Innovation] ...

--- AMENDMENTS ---
[Efficiency] proposes ...

--- VOTING ---
[Safety] votes: REJECT
[Innovation] votes: APPROVE

--- FINAL DECISION ---
Bill Passed: False
Vetoed By: ['Safety', 'Compliance']
```

---

## 🧪 Robustness Features

- If Gemini returns malformed JSON → retried
- If Gemini still fails → agent abstains
- No agent failure can crash the parliament
- All decisions remain valid and auditable
- Strict schema enforcement everywhere

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
- With enforced legitimacy
- With procedural constraints
- With robust LLM integration
- With explainable outcomes

This is research-grade architecture.

---

## 🛣️ Possible Next Directions

Future extensions (not yet implemented):

- Multi-round debates (agents respond to each other)
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
