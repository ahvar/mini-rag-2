# Streaming UI Next Steps

This document tracks the planned frontend follow-up work after the first streamed chat milestone.

## Next Steps

### 1. Extract Inline Chat Logic to a Static JavaScript File

Goal: reduce template complexity before any visual redesign.

Tasks:
- Move the inline script out of `app/templates/index.html` into `app/static/js/chat.js`.
- Keep behavior unchanged during the extraction.
- Update the template to load the external script.
- Keep the logic modular enough to separate message rendering, API calls, and stream reading.

Done when:
- `index.html` contains only the markup and script include.
- Streaming behavior still works exactly as before.

### 2. Refresh the Chat Interface

Goal: replace the default Bootstrap look with a cleaner chat-focused layout.

Tasks:
- Add a dedicated stylesheet, likely in `app/static/css/chat.css`.
- Replace the generic card layout with a more intentional chat shell.
- Improve message spacing, composer layout, and mobile behavior.
- Add clearer states for thinking, streaming, and errors.

Done when:
- The chat interface feels purpose-built rather than default Bootstrap.
- The layout works comfortably on desktop and mobile.

### 3. Add Markdown and Code Formatting for Assistant Messages

Goal: make technical answers easier to read.

Tasks:
- Render assistant content as markdown.
- Add code block styling and syntax highlighting.
- Preserve safe rendering and avoid injecting raw HTML directly.

Done when:
- Lists, headings, inline code, and fenced code blocks render cleanly.
- Code responses are readable without breaking the existing stream flow.

## Prerequisites

- Verify both agent paths stream correctly in the browser before starting any UI refactor.
- Confirm failed requests restore the input and send button cleanly before changing layout or rendering.

## Suggested Order

1. Browser verification
2. JavaScript extraction
3. UI refresh
4. Markdown and code formatting