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
| F-001 Authentication and registration gate | [`F-001-authentication/`](./F-001-authentication/) | In Progress |
| F-019 Persian localization and RTL layout | [`F-019-persian-rtl-auth/`](./F-019-persian-rtl-auth/) | Done |
| F-020 SQLite as the default database | [`F-020-sqlite-default-database/`](./F-020-sqlite-default-database/) | Done |
| F-021 Persian combined auth entry | [`F-021-persian-auth-entry/`](./F-021-persian-auth-entry/) | Done |
| F-022 Admin panel shell | [`F-022-admin-shell/`](./F-022-admin-shell/) | Done |
| F-023 Vazirmatn font | [`F-023-vazir-font/`](./F-023-vazir-font/) | Done |
| F-024 Categories and the admin boundary | [`F-024-categories-admin/`](./F-024-categories-admin/) | Done |
