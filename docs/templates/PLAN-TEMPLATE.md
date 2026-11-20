# Implementation Plan - [F-###] [Feature Name]

- **Status:** Draft / Review / Approved / In Progress / Done
- **Related SPEC:** `SPEC.md`
- **Related ADRs:** [links or "none - because ..."]
- **Owner:** [name or agent]
- **Last updated:** YYYY-MM-DD

---

## 1. Implementation approach

Summarize the design in a few paragraphs. State the module boundaries, the main use cases, and
what is deliberately not being built.

## 2. Preconditions

- [ ] SPEC approved.
- [ ] Task status is `Ready`.
- [ ] Dependencies are Done.
- [ ] Open questions that affect integrity/security/scope are resolved.
- [ ] Required ADRs are accepted or explicitly proposed with a resolution date.
- [ ] Test database is available.

## 3. Ordered TDD tasks

Work in small Red -> Green -> Refactor increments. For each step, list the failing test first.

| # | Step | Files/modules | Test to write first (Red) | Minimum implementation (Green) | Refactor / notes |
|---:|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

### Test-first order

1. Domain rule test.
2. Repository/constraint integration test.
3. API contract and authorization test.
4. Frontend component/composable test.
5. End-to-end journey (when applicable).

Do not write production code before step 1's test fails for the expected reason.

## 4. Database and migration plan

- Tables/columns added or changed:
- Constraints:
- Indexes:
- PostgreSQL-specific features (extension, exclusion constraint, partial index):
- Migration filename and order:
- Data backfill:
- Rollback strategy:
- Migration verification (clean database + previous schema):

## 5. API and frontend plan

### API

- Endpoints:
- Schemas:
- Status codes and error codes:
- Pagination/filtering:
- OpenAPI review notes:

### Frontend

- Routes:
- Pages/components:
- Composables/API wrappers:
- Pinia state (only if shared):
- Loading/empty/error/success states:
- Accessibility checks:
- Responsive behavior:

## 6. Test plan

| Layer | Cases | Tool |
|---|---|---|
| Unit | | pytest |
| Integration | | pytest + PostgreSQL |
| API/contract | | pytest |
| Security | | pytest |
| Concurrency | | pytest + PostgreSQL |
| Frontend unit | | Vitest |
| E2E | | Tool chosen in F-001 |

Also list the exact commands to run and the expected result. Record actual results in the
completion report, not here.

## 7. Observability and operations

- Logs to add (with redaction):
- Metrics to add:
- Audit events:
- Retry/failure behavior:
- Runbook or operational notes:

## 8. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| | | | |

## 9. Rollout and rollback

- Feature flag needed: yes/no
- Deployment order:
- Migration order:
- Rollback steps:
- Data cleanup if rolled back:
- User communication:

## 10. Documentation updates

- [ ] `Task-List.md` updated.
- [ ] Feature `SPEC.md` updated if behavior changed.
- [ ] ADR created or updated.
- [ ] `docs/ARCHITECTURE.md` updated if design changed.
- [ ] `docs/SRS.md` updated if requirements changed.
- [ ] `README.md` updated if setup/commands changed.
- [ ] OpenAPI examples updated.

## 11. Completion checklist

- [ ] All acceptance criteria pass.
- [ ] TDD evidence exists (tests were written first and are meaningful).
- [ ] Unit tests pass.
- [ ] PostgreSQL integration tests pass.
- [ ] Concurrency tests pass where applicable.
- [ ] Authorization negative tests pass.
- [ ] Frontend tests pass.
- [ ] E2E tests pass where applicable.
- [ ] Formatter passes.
- [ ] Linter passes.
- [ ] Type checks pass.
- [ ] Migration upgrade and rollback reviewed.
- [ ] Security/privacy review complete.
- [ ] Docs and `Task-List.md` updated.
- [ ] Completion report includes actual commands and results.
- [ ] Known limitations recorded as follow-up tasks.

## 12. Completion report

Fill this in only after verification. Never fabricate results.

- **What changed:**
- **Commands executed and results:**
- **What was not run and why:**
- **Known limitations:**
- **Follow-up tasks:**
