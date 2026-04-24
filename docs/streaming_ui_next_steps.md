# Streaming UI Next Steps

This document captures the follow-up work after the first streamed chat milestone.

## Current State

- Flask remains the only application server.
- The existing synchronous `/api/chat` route remains available as a fallback.
- The UI in `app/templates/index.html` can consume a streamed response from `/api/chat-stream`.
- Focused API tests for the streaming route are in place.

## Next Steps

### 1. Verify Streaming End-to-End in the Browser

Goal: confirm both agent paths stream correctly in the live app.

Tasks:
- Start the Flask app and test a LinkedIn-style prompt.
- Test a RAG-style technical question.
- Confirm the assistant message updates progressively instead of waiting for the full response.
- Confirm failed requests restore the input and send button cleanly.

Done when:
- Both agents stream visible partial output in the browser.
- No duplicate assistant messages are created.
- Error handling leaves the form usable.

### 2. Extract Inline Chat Logic to a Static JavaScript File

Goal: reduce template complexity before any visual redesign.

Tasks:
- Move the inline script out of `app/templates/index.html` into `app/static/js/chat.js`.
- Keep behavior unchanged during the extraction.
- Update the template to load the external script.
- Keep the logic modular enough to separate message rendering, API calls, and stream reading.

Done when:
- `index.html` contains only the markup and script include.
- Streaming behavior still works exactly as before.

### 3. Refresh the Chat Interface

Goal: replace the default Bootstrap look with a cleaner chat-focused layout.

Tasks:
- Add a dedicated stylesheet, likely in `app/static/css/chat.css`.
- Replace the generic card layout with a more intentional chat shell.
- Improve message spacing, composer layout, and mobile behavior.
- Add clearer states for thinking, streaming, and errors.

Done when:
- The chat interface feels purpose-built rather than default Bootstrap.
- The layout works comfortably on desktop and mobile.

### 4. Add Markdown and Code Formatting for Assistant Messages

Goal: make technical answers easier to read.

Tasks:
- Render assistant content as markdown.
- Add code block styling and syntax highlighting.
- Preserve safe rendering and avoid injecting raw HTML directly.

Done when:
- Lists, headings, inline code, and fenced code blocks render cleanly.
- Code responses are readable without breaking the existing stream flow.

## Suggested Order

1. Browser verification
2. JavaScript extraction
3. UI refresh
4. Markdown and code formatting

## Explicitly Deferred

- React migration
- Vite or other frontend build tooling
- Persistent chat history
- Authentication
- WebSockets
- SSE event typing or richer stream framing