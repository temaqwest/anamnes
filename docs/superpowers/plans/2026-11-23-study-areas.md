# Personal Study Areas Implementation Plan

**Goal:** Add an area while uploading a PDF and rename existing areas from the archive.

**Architecture:** Own areas by account and retain their public slug during renames and migration. Keep the seeded catalogue as the source of initial areas. Share the name form between the upload and archive pages.

**Spec:** The next milestone agreed in the Anamnes chat.

- [x] Test creation, renaming, duplicate names and cross-account access through the API.
- [x] Migrate existing links and implement owner-scoped list, create and rename.
- [x] Connect both screens using the FSD public APIs and add the ADR.
- [x] Verify SQLite, PostgreSQL, browser flows and migration of pre-existing links.
