# Infrastructure

Local PostgreSQL through Docker Compose and the CI workflow exist. Production infrastructure is
not implemented.

## Local PostgreSQL

`compose.yaml` starts PostgreSQL 16 on `127.0.0.1:5432`. It reads `POSTGRES_PASSWORD` from
`.env`. Host port 5432 conflicts with a native PostgreSQL service, so stop that service first.

```powershell
docker compose -f infra/compose.yaml up -d
```

A native PostgreSQL 16 installation is equally valid; create the `beautybook` and
`beautybook_test` databases and the `beautybook_app` role described in the root README.

## Planned for F-001

- Local PostgreSQL via Docker Compose.
- A documented `.env.example` with placeholders only.
- A repeatable way to run the backend and frontend locally.
- A CI workflow for lint, type check, tests, and migration validation.

## Planned for production (F-018)

- Container images for the backend and worker.
- Managed PostgreSQL with backups.
- S3-compatible object storage for salon images.
- Reverse proxy / load balancer with TLS.
- Transactional email provider.
- Centralized logs, metrics, and alerts.
- Documented migration, rollback, backup, and restore procedures.

## Rules

- No real secrets in this repository.
- No environment-specific values hardcoded in application code.
- Infrastructure changes that affect architecture require an ADR.
- Production deployment must have a tested restore path before launch.

See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md), Section 18.
