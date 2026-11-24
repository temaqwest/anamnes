# PDF Search and Compose Implementation Plan

**Goal:** Find text in uploaded PDFs and run the complete stack with Docker Compose.

**Architecture:** Store page text and the indexing state in Django's database. Keep the indexing process separate from requests. Nginx serves the built React client and proxies to Gunicorn. PostgreSQL and PDF files live in separate named volumes.

**Tech stack:** Django, pypdf, PostgreSQL, React, Vite, Nginx and Docker Compose.

**Spec:** [Anamnes product requirements](https://chatgpt.com/space/page_758ecdde86408191a52531d6f5e236d1).

## Global constraints

- Preserve authentication, archive metadata, original PDF bytes and existing URLs.
- Use the existing FSD layer boundaries.
- Copy source and dependency manifests into build contexts. Keep databases, personal PDFs and local secrets outside images.

## Review focus

- Previously uploaded PDFs enter the indexing queue through the migration.
- Search respects owner and area and returns a one-based page number.
- Worker interruptions and retried uploads do not duplicate the index.
- Bringing the Compose project down and back up keeps both database and originals.

## Tasks

- [x] Verify failing tests for page search, ownership and retry. Implement indexing and the API.
- [x] Connect the archive and PDF viewer to search results and indexing status. Verify the frontend build.
- [x] Build and start Compose using a temporary project and test data. Verify indexing and data persistence. Record ADRs and launch instructions.

Verified the Django suite on SQLite and containerized PostgreSQL. A synthetic archive migrated from 0003 was indexed successfully. Chromium opened the matching PDF page, and the search result and original survived Compose down/up.
