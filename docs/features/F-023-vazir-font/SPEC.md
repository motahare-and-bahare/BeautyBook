# Feature Specification - [F-023] Self-hosted Vazirmatn (Vazir) font

**Status:** In Progress (requested by the project owner on 2026-11-24)
**Owning module:** `frontend` / `assets/styles`
**Related:** F-019 (Persian RTL screens). No ADR required - see `PLAN.md` section 1.

## 1. Problem and objective

`tokens.css` already asks for `"Vazirmatn", "Vazir", ... Tahoma, "Segoe UI"`, but the project ships
no font file. On a typical Windows machine none of those Persian-first families exists, so the
product silently renders in Tahoma and every machine shows a different typeface.

Objective: ship the font with the application so the Persian UI looks the same everywhere, works
offline, and makes no third-party request at runtime.

## 2. Actors and permissions

Pure presentation. No actor, role, or endpoint is affected.

## 3. User journeys

1. A visitor opens any page -> the Persian text renders in Vazirmatn on the first paint of the
   styled page, without waiting for a third-party host.
2. The font fails to load (blocked, corrupted, unsupported) -> the existing Persian-capable system
   stack renders the text; no invisible text.

### Failure paths

- Font request 404/500 -> `font-display: swap` keeps the fallback visible.
- Very slow network -> the fallback is shown first and replaced when the font arrives.

## 4. Scope

### In scope

- One variable-weight WOFF2 file of Vazirmatn (the maintained successor of Vazir) in the repository.
- `@font-face` declaration with `font-display: swap` and the full `100 900` weight range.
- Import the declaration from the application entry point.
- Keep the existing `--font-sans` fallback chain.
- Ship the font license text.

### Out of scope

- Any npm dependency or font CDN.
- Subsetting, font-feature tuning, or separate static weight files.
- Changing the visual design, sizes, or spacing.
- Adding a second font family (headings stay Vazirmatn).

## 5. Functional requirements

- **FR-FONT-001 (Must):** the font is served from the application's own origin; no request goes to
  a third-party host.
- **FR-FONT-002 (Must):** `@font-face` declares family `Vazirmatn`, `format("woff2")`, and
  `font-display: swap`.
- **FR-FONT-003 (Must):** weights 100-900 are covered so existing `font-weight: 600/700/800`
  rules render the real face instead of a synthetic bold.
- **FR-FONT-004 (Must):** if the font cannot load, the current fallback stack still applies.
- **FR-FONT-005 (Must):** the license text ships with the font.
- **FR-FONT-006 (Should):** the browser requests the font once and caches it; the production build
  fingerprints the file so a changed font is never served stale.

## 6. Business rules and invariants

- No dependency is added to `package.json`; the asset is versioned in the repository.
- The font license (SIL Open Font License 1.1) must stay next to the file; redistributing the font
  without its license is not allowed.
- Keeping the fallback chain is mandatory: a font must never make text invisible.

## 7. UX and API behaviour

- No API change. First paint uses the fallback, then swaps to Vazirmatn.
- Latin glyphs inside Persian text (emails, numbers) come from the same family, which stays
  consistent with the existing `dir="ltr"` inputs.

## 8. Data impact

One binary asset plus its license. No database, no runtime state.

## 9. Security and privacy

- Self-hosting removes a third-party request, so no visitor IP or referrer is disclosed to a font
  CDN. This is a privacy improvement, not only a performance one.
- A font file is parsed by the browser, so it is only ever taken from this repository, never from
  an untrusted runtime source.

## 10. Edge cases

- Offline development: the font still loads because it is local.
- `prefers-reduced-data` / slow connection: `swap` shows text immediately.
- A user who has a system Vazirmatn installed: the local `@font-face` wins, so rendering is
  identical everywhere.
- Browser without WOFF2 (very old): falls back to the system stack; no broken layout.

## 11. Acceptance criteria

- **AC-1:** `src/assets/styles/fonts.css` declares the family, format, weight range, and `swap`.
- **AC-2:** the referenced WOFF2 exists, starts with the `wOF2` signature, and is served by Vite.
- **AC-3:** `--font-sans` still starts with a Vazirmatn family name and the fallbacks are intact.
- **AC-4:** the OFL license file is present next to the font.
- **AC-5:** `npm run test:unit`, `npm run typecheck`, and `npm run build` pass, and the built CSS
  references a hashed font asset.
- **AC-6:** in a live browser, `document.fonts` reports the family as loaded and the computed
  `font-family` of `body` starts with Vazirmatn.

## 12. Test strategy

- Unit (Vitest, Node `fs`): CSS declarations, weight range, `swap`, the asset signature, the
  license file, and the token stack order.
- Build: assert the emitted CSS points at a `fonts/` asset with a content hash.
- Manual: live check of `document.fonts.check()` and the computed style.

## 13. Open questions

None blocking. If the design later needs a display face, that is a separate decision.
