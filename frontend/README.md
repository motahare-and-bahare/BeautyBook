# Frontend

Vue 3 + TypeScript single-page application for BeautyBook. The foundation and the first
authentication screens are implemented: the Vite project, the router, the Pinia bootstrap, design
tokens, global CSS, a Vitest harness, a typed API client with CSRF handling, the customer
registration page at `/register`, and the login page at `/login`. Both forms are connected to the
live backend (`POST /api/v1/auth/register/customer` and `POST /api/v1/auth/login`). Login shows the
generic invalid-credentials message and the pending, rejected, and suspended account states.

The authentication screens are Persian and right to left: `index.html` declares `lang="fa"` and
`dir="rtl"`, the copy is written in Persian inside the components, and Latin data such as email
addresses keeps `dir="ltr"`. Role and status values from the API are displayed through Persian
labels in `src/modules/auth/labels.ts`. See F-019.

## Planned structure

```text
frontend/
├── src/
│   ├── app/                 # Bootstrap, layouts, global providers
│   ├── router/              # Routes and guards
│   ├── modules/
│   │   ├── auth/            # Login, register, verify, reset
│   │   ├── salons/          # Discovery and public salon pages
│   │   ├── services/        # Service comparison
│   │   ├── booking/         # Slot picker and confirmation
│   │   ├── customer-dashboard/
│   │   ├── owner-dashboard/
│   │   └── admin/
│   ├── components/          # Shared presentational components
│   ├── composables/         # Reusable composition functions
│   ├── services/api/        # Typed HTTP client and endpoint wrappers
│   ├── stores/              # Pinia: shared client state only
│   └── assets/styles/       # Design tokens and global CSS
└── tests/
    ├── unit/                # Vitest + Vue Test Utils
    └── e2e/                 # Browser E2E tests (tool chosen in F-001)
```

## Conventions

- Vue 3 Composition API and `<script setup>`.
- TypeScript everywhere; avoid `any`.
- Typed API wrappers; no scattered raw `fetch` calls.
- Pinia only for genuinely shared state (for example, the signed-in user).
- Every data-driven screen has loading, empty, error, and success states.
- Mobile-first responsive layout.
- Semantic HTML, labels, keyboard navigation, visible focus, and accessible error messages.
- Backend authorization is authoritative; route guards are only a UX convenience.
- Never store long-lived credentials in `localStorage` or `sessionStorage`.
- No secrets in the frontend bundle.

## Styling

Plain CSS with design tokens (CSS custom properties), CSS Grid, Flexbox, and Vue scoped styles.
See ADR-0007.

## Setup

Run from this folder. Node.js 20 or newer is required.

```powershell
npm install
npm run dev
```

The development server runs on `http://127.0.0.1:5173` and proxies `/api` to the backend on
`http://127.0.0.1:8000`.

Verify:

```powershell
npm run test:unit
npm run typecheck
npm run build
```

See:

- [`../AGENTS.md`](../AGENTS.md)
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
- [`../docs/adr/0007-frontend-styling.md`](../docs/adr/0007-frontend-styling.md)
