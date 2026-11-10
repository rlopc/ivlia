---
status: accepted
date: 2026-11-10
---

# LangGraph orchestrates the agents, inside the application layer

## Context and Problem Statement

ivlia's agents need a run loop that can pause for approvals and resume, and that keeps the state of a run in progress ([docs/02](../../02-arquitectura-e-interfaces.md), "Orquestación"; [docs/03](../../03-agentes-y-herramientas.md)). The architecture puts every technology behind a closed list of ports, with dependencies pointing inwards. Where does the orchestration framework fit, and does it get a port?

## Considered Options

- LangGraph in the application layer, used directly, with no adapter that copies its API.
- LangGraph behind a port of its own, with an adapter in `adapters/`.
- An own run loop, without a framework.

The design does not record a comparison with other orchestration frameworks, and this ADR does not make one.

## Decision Outcome

Chosen option: LangGraph in the application layer, used directly. Reasons:

- It provides the interrupts that approvals need and the checkpoints that keep a run in progress, which an own loop would have to rebuild.
- An adapter that copies its API would add a layer with no second implementation behind it, against the rule of abstracting only at real boundaries ([docs/02](../../02-arquitectura-e-interfaces.md), "Principios").

How it is applied:

- LangGraph lives only in `ivlia.application.orchestration`. An import-linter contract forbids `langgraph`, `langsmith` and `langchain_core` everywhere else ([backend.md](../../standards/backend.md#layout-and-layers)).
- The domain defines its own agent state (`ivlia.domain.agents.state`). The application translates it to LangGraph's state on each turn, and callers get domain types back.
- LangSmith tracing, which LangGraph can switch on from an environment variable, is disabled in code ([backend.md](../../standards/backend.md#third-party-telemetry)).

### Consequences

- Good, because interrupts and checkpoints come from a maintained library.
- Good, because the domain and the rest of the code do not depend on LangGraph, so replacing it touches one package.
- Bad, because LangGraph brings `langchain-core` and `langsmith` as dependencies, and with them telemetry that must stay off.
- Bad, because the application code that uses LangGraph follows its API and its changes. The domain-state versus LangGraph-state boundary is revisited in slice 5, with the interrupts ([docs/10](../../10-plan-y-pendientes.md)).
