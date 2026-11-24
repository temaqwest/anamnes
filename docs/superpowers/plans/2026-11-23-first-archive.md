# First Archive Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Upload, verify, save and reopen original PDFs in an authenticated desktop archive.

**Architecture:** A same-origin React client calls a Django REST API. Django stores archive metadata in the database and originals in private file storage.

**Tech stack:** Django, Django REST Framework, PostgreSQL with SQLite for local development, React, TypeScript, Vite and shadcn/ui.

**Spec:** [Anamnes product requirements](https://chatgpt.com/space/page_758ecdde86408191a52531d6f5e236d1).

## Global constraints

- Desktop browser first.
- Upload up to 10 PDFs with editable study date and title and visible original filenames.
- Each signed-in user can access only their own archive.

## Review focus

- Ambiguous or invalid filename dates leave the date field empty.
- Rejected files in a batch can be corrected or retried independently.
- Direct file requests enforce the same ownership checks as the document list.

## Tasks

- [x] Write and run archive API tests for filename suggestions, validation, owner access, sorting and preserving the PDF. Implement the Django app and run the suite again.
- [x] Build the archive, batch upload and document viewer using the session and document endpoints. Verify the frontend build and exercise the browser flow with synthetic PDFs.
- [x] Document local setup and the boundaries of this first implementation.
