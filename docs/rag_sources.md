# RAG Source References Plan

## Goal

Show source references in the UI for RAG responses so users can see which documents informed the answer.

## Recommended Approach

Use a custom response header on `/api/chat-stream` for RAG-only source metadata.

- Keep the streaming body as `text/plain`.
- Gather source metadata in Python during RAG retrieval and reranking.
- Parse the header in JavaScript before consuming the stream.
- Render sources below the finalized assistant message.

This preserves the current streaming contract and avoids adding a second request or a persistence layer.

## Design Decisions

### 1. Should we return sources in a custom header?

Yes. This is the recommended first implementation.

Why:
- It does not change the current stream body format.
- The frontend can read headers before reading the stream.
- Pinecone retrieval happens before the LLM stream starts, so the metadata is already available.

### 2. How does inclusion of this metadata impact streaming format?

With the header approach, it does not change the streaming format.

- Response body stays plain streamed text.
- Response metadata carries the sources separately.
- Existing chunk parsing logic remains simple.

### 3. Should we store sources in a separate state/database and reference by message ID?

No.

Why not:
- There is no existing persistence layer for chat messages.
- It adds coordination complexity without solving a current problem.
- This feature can be implemented entirely within the existing request/response flow.

### 4. Should we modify the stream to include metadata at the end?

Not for the first implementation.

Why not:
- It would require custom parsing of the streamed body.
- It makes the current `text/plain` stream more fragile.
- Headers are simpler and less invasive for the current architecture.

## Implementation Plan

1. Update `docs/streaming_ui_next_steps.md` to remove completed frontend tasks and replace them with a new roadmap item for RAG source references.
2. Update `docs/architecture.md` to document that `/api/chat-stream` still returns `text/plain`, but may include compact metadata in headers for UI-side rendering.
3. Refactor `app/agents/registry.py` so `_build_rag_context()` preserves source metadata from Pinecone matches before reranking.
4. Build a compact `sources` structure with fields like `title`, `url`, and `score`, correlated back from reranked results.
5. Extend `app/agents/agent_types.py` so the normalized response contract can optionally carry `sources` in addition to `context`.
6. Reuse the same source-extraction path for both sync and streaming RAG flows in `app/agents/registry.py`.
7. Keep sync `rag_agent()` returning sources directly in the response object.
8. Update the streaming path so RAG sources are available to the route layer before constructing the streaming response.
9. Add a narrow backend wrapper in `app/api/api_selectors.py` that sets a custom header such as `X-Chat-Sources` for RAG streaming responses only.
10. Preserve `mimetype="text/plain"` and keep the streamed body unchanged.
11. Update `app/static/js/chat_api.js` to read and parse the custom header before returning the stream reader.
12. Extend the assistant message model in `app/static/js/chat.js` so finalized assistant messages can store optional `sources` and `agent`.
13. Update `app/static/js/chat_renderer.js` to render a source section beneath assistant messages when `sources` are present.
14. Ensure LinkedIn messages do not render an empty sources block.
15. Add source styling in `app/static/css/chat.css` that fits the current terminal UI.
16. Add focused backend tests in `tests/test_api_selectors.py` that verify:
    - successful RAG streaming still returns `text/plain`
    - `X-Chat-Sources` is present for RAG
    - `X-Chat-Sources` is absent for LinkedIn
    - invalid requests still fail before external calls
17. Add a narrow UI validation pass by rendering `/` through the Flask app factory and verifying the source section hooks are present.
18. Manually verify that RAG responses stream normally and show clickable sources with scores after completion.
19. Manually verify that LinkedIn responses stream normally and show no sources section.

## Relevant Files

- `docs/streaming_ui_next_steps.md`
- `docs/architecture.md`
- `app/agents/registry.py`
- `app/agents/agent_types.py`
- `app/api/api_selectors.py`
- `app/static/js/chat_api.js`
- `app/static/js/chat.js`
- `app/static/js/chat_renderer.js`
- `app/static/css/chat.css`
- `tests/test_api_selectors.py`

## Verification

1. Run focused API tests with the repo `PYTHONPATH` configured.
2. Confirm the streaming route still returns `text/plain` for successful requests.
3. Confirm the custom header is present only for RAG responses.
4. Smoke-test `/` through the Flask app factory.
5. Verify in the browser that a RAG response streams normally, then shows sources after completion.
6. Verify in the browser that a LinkedIn response streams normally with no sources section.

## Rejected Alternatives

### End-of-stream metadata in the body

Rejected for now because it complicates the plain-text stream parser.

### Separate metadata endpoint keyed by message ID

Rejected for now because there is no persistence layer and it adds unnecessary moving parts.

### Switching the stream to framed JSON or event format

Rejected for now because the current implementation already works with `text/plain` and the goal is to preserve that contract.

## Further Considerations

1. Keep the header payload compact by limiting sources to the reranked top results.
2. Prefer a stable display title order such as `metadata.title`, then `metadata.source`, then URL hostname, then `Untitled`.
3. If header size becomes a problem later, revisit an event-framed stream or a follow-up metadata endpoint.
