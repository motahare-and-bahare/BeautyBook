# ADR-0004: UTC Instants and IANA Timezones for Scheduling

- **Status:** Accepted
- **Date:** 2026-11-16

## Context

Providers define recurring availability in local civil time, while customers may be in other timezones. Daylight-saving transitions create ambiguous and nonexistent local times.

## Decision

Persist appointment instants in UTC. Store provider and user timezone preferences as IANA timezone identifiers. Interpret recurring weekly availability in the provider's timezone and convert candidate intervals to UTC for persistence and overlap comparison. Define explicit behavior for ambiguous/nonexistent local times in the availability feature specification.

## Consequences

- Do not store naive timestamps for appointments.
- Use a maintained timezone-aware library.
- Test daylight-saving gaps, repeated times, and cross-timezone display.
- API contracts must distinguish UTC instants from local schedule rules.
