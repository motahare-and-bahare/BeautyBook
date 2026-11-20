# ADR-0007: Frontend Styling with Plain CSS and Design Tokens

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook needs a modern, responsive, accessible interface. The required stack already includes
Vue 3, TypeScript, Vite, Vue Router, and Pinia. The project owner asked for a modern responsive CSS
approach without adding unnecessary major technologies.

Options include a utility CSS framework, a component library, or plain CSS with a small design
system.

## Decision

Use **plain CSS with design tokens** for the first release:

- CSS custom properties for color, spacing, typography, radius, shadows, and breakpoints.
- Mobile-first responsive layout using CSS Grid and Flexbox.
- Scoped component styles in Vue single-file components.
- A small global stylesheet for reset, tokens, and base typography.
- Semantic HTML and accessible focus styles as part of the design system.

No Tailwind, Bootstrap, Vuetify, or other UI framework is added in the first release.

## Alternatives considered

1. **Tailwind CSS.** Excellent utility workflow, but adds a build-level dependency and a new
   vocabulary before the team has proven the design. It can be adopted later with an ADR.
2. **A component library (Vuetify, PrimeVue, Element Plus).** Speeds up standard components, but
   imposes a visual language, adds dependency weight, and makes custom salon branding harder.
3. **CSS Modules.** Viable, but Vue's scoped styles already provide component isolation for this
   project size.
4. **No design system at all.** Rejected: leads to inconsistent spacing, colors, and accessibility.

## Consequences

Positive:

- No extra major dependency.
- Full control over the salon marketplace look and feel.
- Design tokens make future theming and dark mode feasible.
- Easy for a learning developer to inspect and understand.

Negative and risks:

- More handwritten CSS than a utility framework.
- Requires discipline to avoid one-off values; tokens must be used consistently.
- Complex widgets (date pickers, dialogs) may eventually justify a small headless library. That
  requires a dependency review and an ADR if material.

## References

- `docs/ARCHITECTURE.md`, Section 14.3.
- `AGENTS.md`, Section 8.
