# Archive Roadmap Implementation Plan

**Goal:** Finish the agreed document categories, timeline, medications, mobile PWA, scan OCR and archive transfer.

**Spec:** [Working Anamnes requirements](https://chatgpt.com/space/page_758ecdde86408191a52531d6f5e236d1) and the development roadmap agreed in chat.

**Architecture:** Keep the archive's existing API, document access and FSD structure. Share categorization between the archive and timeline. Add medications as an owner-scoped app. OCR remains in the document worker, and data transfer is an explicit offline operation.

- [x] Persist document categories and render category icons and labels in upload, archive and document screens.
- [x] Add a calendar-day timeline driven by archive filters and link to matching PDF pages.
- [x] Integrate the medication lifecycle, including its private history.
- [x] Adapt the web interface to phones and verify installability and the private cache boundary.
- [x] Verify local OCR and the SQLite-to-PostgreSQL transfer with synthetic fixtures.
- [x] Verify the integrated release, update the ADR index and migrate the local development database.

The local development archive remains on SQLite. The transfer was verified in an isolated Compose project using a synthetic archive.
