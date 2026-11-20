# Architecture Decision Records

This folder contains the architectural decisions that shape BeautyBook.

## What is an ADR?

An Architecture Decision Record is a short document that captures:

- the situation that required a decision,
- the decision that was made,
- the alternatives that were considered,
- the consequences and trade-offs.

It is a historical record. If a decision changes, create a new ADR that supersedes the old one
rather than rewriting history.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-monolith.md) | Start with a modular monolith | Accepted |
| [0002](0002-database-strategy.md) | PostgreSQL main, SQLite only for lightweight tests | Accepted |
| [0003](0003-booking-concurrency.md) | Booking overlap prevention strategy | Proposed |
| [0004](0004-timezone-model.md) | UTC instants and IANA timezones | Accepted |
| [0005](0005-authentication-session-strategy.md) | Browser authentication and session strategy | Accepted |
| [0006](0006-image-storage.md) | Image storage strategy | Proposed |
| [0007](0007-frontend-styling.md) | Plain CSS with design tokens | Accepted |
| [0008](0008-money-representation.md) | Money representation and currency scope | Accepted |
| [0009](0009-authorization-model.md) | Role and ownership authorization model | Accepted |
| [0010](0010-role-assignment.md) | Registration flows, role assignment, and administrator provisioning | Accepted |

## When an ADR is required

Create an ADR when a decision changes:

- system boundaries or module ownership,
- persistence, consistency, or concurrency behavior,
- security or privacy posture,
- deployment or infrastructure,
- an external integration or long-lived dependency,
- a major frontend technology or design system.

If no ADR is needed, state why in the feature `PLAN.md`.

## How to write one

1. Copy `docs/templates/ADR-TEMPLATE.md`.
2. Name it `NNNN-short-title.md` with the next number.
3. Set the status (`Proposed`, `Accepted`, `Rejected`, or `Superseded`).
4. Fill in context, decision, alternatives, consequences, and references.
5. Add it to the index above.
6. Link it from the feature SPEC/PLAN.

## Status meanings

- **Proposed:** under discussion; not yet binding.
- **Accepted:** the current agreed decision.
- **Rejected:** considered and not chosen; kept for context.
- **Superseded:** replaced by a newer ADR; the newer one is linked.

## Rules

- Never delete an accepted ADR.
- Never silently edit an accepted decision to mean something different.
- Keep ADRs short enough to read.
- Record the trade-off honestly, including the downsides.
