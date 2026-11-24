# PDF Comparison Implementation Plan

**Goal:** Compare two original PDFs and replace either selection independently.

**Architecture:** Pass the pair and archive filters in the comparison URL. Reuse the archive ordering and PDF.js viewer. Keep page, zoom and scroll state inside each viewer instance.

**Spec:** [Anamnes product requirements](https://chatgpt.com/space/page_758ecdde86408191a52531d6f5e236d1), PDF comparison.

- [x] Add regression checks for unavailable links and skipping the document shown in the other pane.
- [x] Add selection from the filtered archive and compose the comparison page from independent viewers.
- [x] Record the navigation contract in an ADR and verify the browser workflow, including the untouched pane's scroll position.
