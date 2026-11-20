# Feature Specification - [F-###] [Feature Name]

- **Status:** Draft / Review / Approved
- **Owner:** [name or agent]
- **Task-List entry:** [F-###](../../Task-List.md)
- **Module(s):** [identity / salons / services / portfolio / availability / bookings / notifications / administration]
- **Related ADRs:** [links or "none"]
- **Last updated:** YYYY-MM-DD

---

## 1. Problem and objective

What user problem is being solved, and why now? Describe the current limitation and the outcome
this feature must produce. Keep it short and concrete.

## 2. Actors and permissions

Who uses this feature? What may each actor do? What is explicitly forbidden?

| Actor | Allowed | Forbidden |
|---|---|---|
| Public visitor | | |
| Customer | | |
| Salon owner | | |
| Administrator | | |

State the ownership rule explicitly. A role check alone is usually not enough.

## 3. User journeys

Describe the primary journey step by step. Then list alternative paths and failure paths.

### Primary journey

1.
2.
3.

### Alternative paths

-

### Failure paths

-

## 4. Scope

### In scope

-

### Out of scope

-

### Non-goals

-

## 5. Functional requirements

Use unique, testable "shall" statements. Prefix with the feature area, for example `FR-SAL-001`.

- **FR-XXX-001:** The system shall ...
- **FR-XXX-002:** The system shall ...

## 6. Business rules and invariants

List rules that must always hold, including state transitions, calculations, time and money rules,
and consistency requirements.

- **BR-001:** ...
- **BR-002:** ...

If a rule already exists in `docs/SRS.md`, reference it instead of redefining it differently.

## 7. UX and API behavior

### UI

- Pages/screens:
- Loading state:
- Empty state:
- Error state:
- Success state:
- Accessibility notes:
- Responsive behavior:

### API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| | | | |

Request/response schemas, validation rules, status codes, pagination, and error codes:

-

## 8. Data impact

- New entities/tables:
- Changed entities/fields:
- Constraints and indexes:
- Migration required: yes/no
- Backfill required: yes/no
- Retention/deletion behavior:
- Sensitive data:

## 9. Security and privacy

- Authentication requirements:
- Authorization and ownership checks:
- Input validation:
- Rate limiting:
- File upload handling (if applicable):
- Logging and redaction:
- Audit requirements:
- Privacy impact:

## 10. Edge cases

List boundary conditions and tricky scenarios:

- empty/null values,
- duplicate requests,
- concurrent requests,
- timezone and DST boundaries,
- expired sessions or tokens,
- stale availability,
- upload limits,
- partial failures,
- large lists/pagination,
- suspended or unpublished salons,
- deactivated services.

## 11. Acceptance criteria

Use Given/When/Then or an equally objective format. Each criterion must be testable.

### AC-1

**Given** ...
**When** ...
**Then** ...

### AC-2

**Given** ...
**When** ...
**Then** ...

## 12. Test strategy

| Layer | What will be tested | Tool |
|---|---|---|
| Unit | | pytest |
| Integration | | pytest + PostgreSQL |
| API/contract | | pytest |
| Security | | pytest |
| Concurrency | | pytest + PostgreSQL |
| Frontend unit | | Vitest |
| E2E | | Tool chosen in F-001 |

Explicitly state if a layer is not applicable and why.

## 13. Dependencies and open questions

### Dependencies

-

### Open questions

| Question | Why it matters | Owner | Resolution |
|---|---|---|---|
| | | | |

Do not start implementation while a question that affects data integrity, security, or scope is
unresolved.

## 14. Decision log

| Decision | Options considered | Chosen | Rationale | ADR |
|---|---|---|---|---|
| | | | | |

## 15. Definition of Ready

- [ ] Task registered in `Task-List.md`.
- [ ] Actors, permissions, and ownership rules defined.
- [ ] User journeys and failure paths defined.
- [ ] In-scope and out-of-scope items explicit.
- [ ] Acceptance criteria are measurable.
- [ ] Data, API, security, and privacy impact identified.
- [ ] Required ADRs created, or reason for none recorded.
- [ ] Test strategy defined, including PostgreSQL/concurrency where relevant.
- [ ] SPEC and PLAN reviewed and approved.
