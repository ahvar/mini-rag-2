# Streaming UI Status

This document tracks the current state of the streamed chat UI after the initial frontend refactor work.

## Completed Milestones

### 1. Extracted Chat Logic

- The browser chat logic now lives in `app/static/js/chat.js`.
- API concerns and rendering concerns are split into `chat_api.js` and `chat_renderer.js`.

### 2. Refreshed Chat Interface

- The terminal-style interface now uses `app/static/css/chat.css`.
- The Flask template remains lightweight and focused on structure.

### 3. Added Markdown and Code Formatting

- Assistant responses render markdown-like formatting without injecting raw HTML.
- Fenced code blocks, headings, lists, inline code, and links render in the streamed chat view.

### 4. Added RAG Source References

- `/api/chat-stream` still streams `text/plain`.
- RAG-specific source metadata is delivered separately through `X-Chat-Sources`.
- The UI renders source references only after the assistant response is complete.

## Current Follow-Up Ideas

1. Add browser-level automation for the streaming transcript and source rendering flow.
2. Improve accessibility cues for streamed updates and source sections.
3. Consider richer source previews only if header size or UX needs justify a different transport.
