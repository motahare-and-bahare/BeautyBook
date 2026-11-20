# ADR-0008: Money Representation and Currency Scope

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook displays and compares service prices, stores price snapshots on bookings, and may later
support deposits or payments. Prices must be exact, comparable, and stable over time.

Binary floating point cannot represent most decimal money values exactly. For example, `0.1 + 0.2`
is not exactly `0.3` in IEEE 754 arithmetic. Rounding drift is unacceptable in a marketplace.

The first release also needs a simple currency model. Supporting many currencies per salon or
live exchange-rate conversion adds substantial product and accounting complexity.

## Decision

- Store money as **integer minor units** (for example, cents) plus an **ISO 4217 currency code**.
- In the MVP, the **salon** owns the currency. Services are priced in the salon's currency.
- Store the price, currency, service name, and duration as a **snapshot** on each booking.
- Never use `float` or a binary floating-point column for money.
- Format money for display only at the presentation boundary.
- Do not perform currency conversion in the first release.
- Do not change a salon's currency while it has active services or bookings without a documented
  migration and product decision.
- When payments are added, the payment feature must define minor-unit handling, provider
  constraints, refunds, and reconciliation in its own ADR.

## Alternatives considered

1. **Decimal columns and Python `Decimal`.** Exact and viable, but adds conversion and
   serialization decisions. Integer minor units are simpler and map directly to payment providers.
2. **Floating-point columns.** Rejected: unsafe for money.
3. **One currency per service.** Rejected for the MVP: complicates comparison and reporting
   without a proven need.
4. **Multi-currency with exchange rates.** Rejected for the first release: requires rate sources,
   historical rates, rounding rules, and accounting review.

## Consequences

Positive:

- Exact arithmetic for prices.
- Easy comparison across services in the same salon.
- Snapshots preserve what the customer agreed to.
- A clear path to payment-provider integration.

Negative and risks:

- Every layer must agree that a price is in minor units. Names and documentation must say so
  explicitly.
- Zero-decimal currencies (for example, JPY) need careful formatting; do not assume two decimals.
- A salon changing currency later is a data-migration problem, not a simple edit.
- Multi-currency marketplaces will need a future ADR.

## Verification

- A price of `1999` in `EUR` displays as `19.99`.
- A price of `1999` in `JPY` is formatted according to the currency's minor-unit rules.
- Booking creation copies the price and currency snapshot.
- A later service price change does not alter an existing booking.
- Database tests reject negative prices and floating-point input.

## References

- `docs/SRS.md`, BR-011, FR-SVC-002, FR-BKG-004.
- `docs/ARCHITECTURE.md`, Sections 8 and 12.1.
- `AGENTS.md`, Section 7.
