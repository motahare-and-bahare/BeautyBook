# ADR-0006: Image Storage Strategy

- **Status:** Proposed - must be finalized before F-006 implementation
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

Salon owners upload a cover photo and portfolio images. These files are:

- user-generated and potentially malicious,
- potentially large,
- public once the salon is published,
- not relational data that belongs in the main database,
- subject to privacy concerns such as embedded location metadata.

Storing uploads in the application source tree or serving them directly from a user-controlled
path is unsafe.

## Decision (recommended)

Use a **storage adapter** with two implementations:

- **Local development:** filesystem directory outside the web root, configured by an environment
  variable.
- **Production:** S3-compatible object storage (for example, an S3 bucket or a compatible
  provider), configured by environment variables and least-privilege credentials.

Store only metadata in PostgreSQL (`salon_photos`: storage key, content type, dimensions, byte
size, alt text, sort order, cover flag, deletion state).

Upload pipeline:

1. Authenticate the salon owner and verify salon ownership.
2. Enforce request size limits before reading the whole body.
3. Inspect file signatures/magic bytes, not just the extension or client MIME type.
4. Decode the image with a maintained library.
5. Re-encode to a safe format and strip EXIF/location metadata.
6. Generate a random storage key; never use the original filename.
7. Write the object through the storage adapter.
8. Insert metadata in a transaction.
9. Serve through a controlled endpoint or object-storage origin with appropriate caching.

Deletion is soft-first: mark the metadata deleted, remove it from public output, and clean up the
stored object asynchronously.

## Alternatives considered

1. **Store images as database blobs.** Rejected: bloats backups, complicates serving, and is a poor
   fit for public media.
2. **Store in the frontend/public folder.** Rejected: mixes user content with deployable code and
   creates path and overwrite risks.
3. **Serve directly from user-supplied filenames.** Rejected: path traversal and enumeration risk.
4. **Add an image CDN immediately.** Deferred: unnecessary before real traffic; the adapter keeps
   the option open.

## Consequences

Positive:

- Clear separation between metadata and bytes.
- Testable adapter contract.
- Safer upload handling.
- Production can scale storage independently.

Negative and risks:

- Extra configuration and credentials.
- Local and production behavior differ; integration tests must cover the adapter.
- Image processing adds CPU cost and dependency weight.
- Orphaned objects require a cleanup process.

## Verification

- Reject a file whose bytes are not an allowed image type even if its name ends in `.jpg`.
- Reject oversized files.
- Reject attempts to use `../` or absolute paths.
- Confirm only the owning salon can mutate its images.
- Confirm EXIF location data is removed from served public images.
- Confirm a failed upload leaves no metadata row.

## References

- `docs/ARCHITECTURE.md`, Section 10.2.
- `docs/SRS.md`, FR-IMG-001 to FR-IMG-010.
- `AGENTS.md`, Sections 9.4 and 11.
