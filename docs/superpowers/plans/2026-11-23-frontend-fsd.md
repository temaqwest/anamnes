# Frontend FSD Migration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan in order.

**Goal:** Adopt Feature-Sliced Design and record the project's architecture decisions for manual contributors.

**Architecture:** Keep each screen in its own page slice. Centralize study and session contracts in entities and keep transport and UI primitives in shared. Wire routing and the private workspace in app.

**Tech stack:** React, TypeScript, Vite, shadcn/ui and Steiger.

**Spec:** [Existing product requirements](https://chatgpt.com/space/page_758ecdde86408191a52531d6f5e236d1) and the request to use FSD and record ADRs.

## Global constraints

- Preserve the existing desktop flows and API contract.
- Keep the domain-independent UI kit in Shared.

## Review focus

- Cross-slice imports resolve through public APIs.
- Upload retries and study edits still preserve the original PDF.
- Browser navigation keeps archive filters and continues to enforce session access.

## Tasks

- [x] Run the official Steiger rules against the original source tree and record the baseline.
- [x] Move the app entry point and each screen to their FSD locations. Extract shared request handling, study contracts and session operations. Update shadcn aliases.
- [x] Add ADRs for the stack, frontend structure and PDF import. Link them from the README.
- [x] Verify Steiger, build, backend tests and the existing Chromium scenario.

The original source failed Steiger on the top-level `lib` directory. The migrated source passes the recommended FSD rules with warnings treated as errors.
