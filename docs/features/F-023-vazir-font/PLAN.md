# Implementation Plan - [F-023] Self-hosted Vazirmatn (Vazir) font

## 1. Approach

Add one variable WOFF2 file to `src/assets/fonts/`, declare it once in
`src/assets/styles/fonts.css`, and import that stylesheet before the tokens. The existing
`--font-sans` chain already lists Vazirmatn first, so no component changes.

Why the variable file instead of five static weights: the UI uses 400, 600, 700, and 800. Five
separate files would mean five requests (or five `@font-face` blocks) for one typeface; the variable
file is ~110 KB and covers the whole 100-900 range. Fewer files, one cache entry, no synthetic bold.

Why self-hosted instead of a CDN or `@fontsource/*`: `AGENTS.md` forbids casual dependencies, and a
CDN would disclose every visitor's IP to a third party. One static asset with its license is the
smallest correct option.

No ADR: no dependency, no persistence, no module boundary, no security posture change beyond
dropping a third-party request that never existed.

**Naming:** the family the project asked for ("وزیر") is today released as **Vazirmatn**, the
maintained continuation of Vazir by the same designer. The CSS family name is `Vazirmatn`, and the
old name stays in the fallback chain for machines that have it installed.

## 2. Ordered TDD tasks

1. **Red -** `tests/unit/fonts.spec.ts`:
   - `fonts.css` exists and declares `font-family: "Vazirmatn"`, `format("woff2")`,
     `font-weight: 100 900`, and `font-display: swap`;
   - the referenced WOFF2 exists, is larger than 20 KB, and starts with `wOF2`;
   - `Vazirmatn-OFL.txt` exists next to it;
   - `tokens.css` keeps `"Vazirmatn"` first and `Tahoma` in the fallbacks;
   - `main.ts` imports the font stylesheet before the tokens.
2. **Green -** download the official variable WOFF2 and the OFL text; add `fonts.css`; import it.
3. **Refactor -** keep the `@font-face` block in one file and document the version in a comment.
4. **Verify -** unit tests, typecheck, build, then a live browser check of `document.fonts` and the
   computed `font-family`.

## 3. API and data plan

None. `GET /fonts/Vazirmatn-Variable.<hash>.woff2` is a static asset emitted by Vite.

## 4. Test plan

| Layer | What |
|---|---|
| Unit (fs) | declarations, weight range, `swap`, asset signature, size, license, token order, import order |
| Build | emitted CSS references a hashed `fonts/` asset |
| Live | `document.fonts.check('16px Vazirmatn')`, computed style, zero third-party requests |

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Font makes text invisible while loading | `font-display: swap` plus the existing fallback chain |
| Invisible or slow first paint on mobile data | one 110 KB variable file, cached with a content hash |
| License violation | `Vazirmatn-OFL.txt` versioned next to the font |
| Package size | one file, no extra weights, no icon font |
| Build silently drops the asset | a test asserts the asset bytes and the emitted CSS reference |

## 6. Rollout and rollback

Rollback = delete `fonts.css`, the font folder, and the import line. The token stack already had a
Vazirmatn-first list before this task, so nothing else changes.

## 7. Documentation

- `Task-List.md`: F-023 row and change-log entry.
- `README.md` / `frontend/README.md`: the font is shipped, its license, and how to update it.
- F-019 SPEC keeps its claim that the font stack is Persian-first; this task makes it real.

## 8. Completion checklist

- [x] Tests written first and observed failing
- [x] Font served from the app origin, no CDN
- [x] `swap` and full weight range declared
- [x] License file shipped
- [x] Fallback chain unchanged
- [x] `test:unit`, `typecheck`, `build` clean
- [x] Live check done
- [x] Task-List and README updated

## 9. Completion report (2026-11-24)

**Delivered**

| File | Detail |
|---|---|
| `src/assets/fonts/Vazirmatn-Variable.woff2` | 111,152 bytes, signature `wOF2`, upstream v33.0.3 |
| `src/assets/fonts/Vazirmatn-OFL.txt` | SIL Open Font License 1.1, shipped with the font |
| `src/assets/styles/fonts.css` | one `@font-face`: `Vazirmatn`, `100 900`, `swap`, local `url()`, `unicode-range` |
| `src/main.ts` | imports `fonts.css` before `tokens.css` |
| `src/assets/styles/tokens.css` | comment updated; the stack was already Vazirmatn-first and stays unchanged |
| `tests/unit/fonts.spec.ts` | 6 file-level guards |

**Why Vazirmatn and not "Vazir"**: the design is the same typeface; upstream renamed the family to
Vazirmatn when it became a variable font. Updating an old static Vazir would ship four extra files
and miss the fixes. The old name stays in the fallback chain, so nothing depends on the rename.

**Red -> Green evidence**

1. Red: `fonts.spec.ts` failed with `ENOENT ... fonts.css`, missing WOFF2, missing license, and a
   missing `main.ts` import.
2. Green: after the asset, the stylesheet, the import, and the token comment, the file passed.
3. One test was tightened rather than weakened: the "no third-party request" assertion now targets
   `url(...)` and `@import` only, so the upstream project link inside a comment is allowed while a
   real remote load still fails the test.

**Commands actually run**

| Command | Result |
|---|---|
| `& 'C:\Program Files\nodejs\npm.cmd' run test:unit -- tests/unit/fonts.spec.ts` | Red first (5 of 6 failed), then 6/6 green |
| `& 'C:\Program Files\nodejs\npm.cmd' run test:unit` | 12 files, 80 tests passed |
| `& 'C:\Program Files\nodejs\npm.cmd' run build` | 66 modules; emitted `dist/assets/Vazirmatn-Variable-BeciDpKm.woff2` |
| grep on the built CSS | `@font-face{font-family:Vazirmatn;font-weight:100 900;font-display:swap;src:url(/assets/Vazirmatn-Variable-BeciDpKm.woff2)` |
| live browser on `/auth` | `document.fonts` entry `Vazirmatn 100 900` status `loaded`; `check('16px Vazirmatn') === true`; `body` computed family starts with Vazirmatn; one local `.woff2` request, no external font request |

**Not run / known limits**

- No visual regression tool exists in the project, so "the text looks right" was judged by eye on a
  screenshot, not pixel-diffed.
- The font is not subsetted: the file carries Latin and Arabic ranges in one 111 KB request. If the
  bundle budget ever matters, subsetting is a follow-up task, not a silent change.
- `font-weight: 100 900` requires a variable-font capable browser. Older browsers fall back to the
  system stack; they are not broken, just not branded.
