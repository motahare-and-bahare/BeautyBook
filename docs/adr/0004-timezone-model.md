# ADR-0004: UTC Instants and IANA Timezones

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

Salons define working hours in local civil time. Customers may be in a different timezone.
Daylight-saving transitions create local times that do not exist (spring forward) or occur twice
(fall back).

Storing a naive local timestamp makes an appointment ambiguous. Treating every time as UTC makes
working hours wrong. The system needs a clear separation between instants and schedule rules.

## Decision

- Persist appointment instants in **UTC** using timezone-aware values (`timestamptz` in
  PostgreSQL).
- Persist salon working hours as **local wall-clock times** plus the salon's **IANA timezone**
  identifier (for example, `Europe/Berlin`).
- Use `zoneinfo` (or an equivalent maintained library) for conversion. Do not hand-roll timezone
  math.
- Convert candidate slots to UTC before comparison and persistence.
- API responses include UTC instants, the salon timezone, and display-ready local values.
- Customer-facing times are shown in a clearly stated timezone.
- DST policy:
  - nonexistent local times are skipped,
  - ambiguous local times use the first occurrence (`fold=0`),
  - the policy is tested for both spring-forward and fall-back dates.

## Alternatives considered

1. **Store local naive timestamps.** Rejected: ambiguous across timezones and DST.
2. **Store everything in UTC, including working hours.** Rejected: working hours are civil-time
   rules; a 09:00 opening must remain 09:00 after a DST change.
3. **Store a fixed UTC offset per salon.** Rejected: offsets change with DST; an IANA timezone is
   required.
4. **Convert in the browser only.** Rejected: the backend must be authoritative for availability
   and booking.

## Consequences

Positive:

- Appointments have one unambiguous instant.
- Working hours behave correctly across DST.
- Cross-timezone display is predictable.

Negative and risks:

- Every developer must understand the instant vs local-rule distinction.
- Tests must include DST boundaries.
- Changing a salon's timezone affects future interpretation of working hours and must be handled
  carefully.

## References

- `docs/ARCHITECTURE.md`, Sections 11.1-11.4.
- `docs/SRS.md`, BR-008 to BR-010.
- `AGENTS.md`, Section 10.
