# Feature Documents

Every feature gets its own folder here:

```text
docs/features/<TASK-ID>-<short-name>/
├── SPEC.md
└── PLAN.md
```

Examples:

```text
docs/features/F-001-authentication/
docs/features/F-004-salon-profile/
docs/features/F-009-booking/
```

## Rules

1. **Register first.** The feature must already exist in `Task-List.md`.
2. **Write the SPEC before the plan.** The SPEC defines the problem, scope, behavior, and
   acceptance criteria. The PLAN describes how to build it.
3. **No empty placeholders.** A folder is created when the feature enters specification, not in
   advance, and its documents must contain real content.
4. **Review before implementation.** The task moves to `Ready` only after both documents are
   approved.
5. **Keep them current.** If implementation reveals a necessary design change, update the SPEC and
   PLAN and record a material decision in an ADR.
6. **Link the evidence.** At completion, the PLAN's completion report records the commands that
   were actually run and their results.

## Templates

- [`SPEC-TEMPLATE.md`](../templates/SPEC-TEMPLATE.md)
- [`PLAN-TEMPLATE.md`](../templates/PLAN-TEMPLATE.md)
- [`ADR-TEMPLATE.md`](../templates/ADR-TEMPLATE.md)

## Current feature documents

| Task | Folder | Status |
|---|---|---|
| F-001 Authentication and registration gate | [`F-001-authentication/`](./F-001-authentication/) | Ready (approved 2026-11-18) |
