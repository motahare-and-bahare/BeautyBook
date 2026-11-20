# ADR-0001: Start with a Modular Monolith

- **Status:** Accepted
- **Date:** 2026-11-16

## Context

The product is an early-stage scheduling platform. Core workflows require strongly consistent transactions across availability and booking data. The team needs rapid iteration and manageable operational complexity.

## Decision

Build the backend as a modular monolith with explicit domain boundaries and one primary relational database. Do not introduce microservices in the initial releases.

## Consequences

- Simpler deployment, debugging, and transactional consistency.
- Clear module boundaries preserve future extraction options.
- Modules must avoid cross-domain database shortcuts and cyclic dependencies.
- A service extraction requires a new ADR supported by measurable scaling or organizational needs.
