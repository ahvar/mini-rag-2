# LangSmith Observability Implementation Plan

This document captures the agreed implementation plan for adding LangSmith observability to this repository before code changes begin.

For the current system shape, request flow, shared contracts, and tracing-relevant boundaries, see `agent_docs/project-architecture-reference.md`.

## Scope

- Keep the current Flask application architecture.
- Do not migrate the app to the OpenAI Agents SDK as part of this change.
- Add LangSmith observability around the existing OpenAI- and Pinecone-based pipeline.
- Centralize OpenAI client construction so tracing can be applied consistently.

## Agreed Direction

### 1. Add a shared wrapped OpenAI client module

Create a small integration module, likely `app/lib/openai_client.py` or `app/integrations/openai.py`, that:

- constructs the base `OpenAI` client from `Config.OPENAI_API_KEY`
- wraps it with LangSmith's `wrap_openai(...)`
- exports the wrapped client for reuse across the app

This is the Python equivalent of the TypeScript `wrapOpenAI` pattern discussed earlier.

### 2. Refactor direct OpenAI call sites to use the shared client

Replace inline client construction in the existing direct OpenAI call sites:

- `app/api/api_selectors.py`
- `app/agents/registry.py`
- `app/agents/linkedin.py`

with imports from the shared wrapped client module.

Goal: every direct OpenAI chat completion or structured parse call goes through one traced client.

### 3. Keep current request and response boundaries

Do not change:

- Flask route contracts
- `AgentRequest` / `AgentResponse` / `StreamingAgentResponse`
- current selector flow
- current Pinecone retrieval flow

The initial LangSmith change is an observability and client-centralization refactor, not an orchestration rewrite.

### 4. Add pipeline-level tracing around non-OpenAI steps

The wrapped OpenAI client will trace direct OpenAI client calls, but it will not automatically make the whole RAG pipeline observable.

Add explicit tracing around the app-owned workflow boundaries so one request can be inspected end-to-end. At minimum, trace these steps:

- agent selection
- embedding generation
- Pinecone query
- reranking
- final answer generation

This tracing should live in the existing execution functions rather than in Flask routes.

### 5. Keep provider flexibility as a follow-up concern

The shared client module is a good first step toward provider flexibility, but it does not fully abstract provider differences.

Important limitation:

- swapping OpenAI for another provider is easy only for the direct generation calls
- embeddings, structured parsing, and model capability differences may still require a higher-level provider abstraction later

This means the wrapped base-client pattern is reasonable, but it is not by itself a complete multi-provider architecture.

## Expected Coverage

After the shared wrapped client refactor, LangSmith traces should appear for the direct OpenAI calls currently made in:

- `app/api/api_selectors.py`
- `app/agents/registry.py`
- `app/agents/linkedin.py`

Additional instrumentation will still be needed for:

- LangChain embeddings
- Pinecone query and rerank operations
- top-level request spans that connect the full pipeline together

## Risks

### Partial migration risk

If any module continues instantiating its own raw `OpenAI(...)` client, observability will be incomplete and traces will be inconsistent.

### Coverage gap risk

Wrapping the OpenAI client does not automatically trace:

- LangChain embeddings
- Pinecone operations
- app-specific orchestration steps

Without explicit pipeline tracing, LangSmith will show isolated model calls instead of a coherent end-to-end RAG request.

### Abstraction risk

The shared client pattern improves reuse and tracing, but it does not fully solve provider portability. A future provider abstraction may still be needed if the app must support non-OpenAI generation and embeddings cleanly.

### Test seam changes

Tests that mock inline client creation may need to be updated once client construction is centralized in a shared module.

## Non-Goals For The First Change

- Migrating to the OpenAI Agents SDK
- Rewriting the RAG orchestration model
- Changing API response formats
- Replacing LangChain embeddings
- Replacing Pinecone

## Implementation Order

1. Add a shared wrapped OpenAI client module.
2. Refactor all direct `OpenAI(...)` call sites to import that module.
3. Validate that direct OpenAI traces appear in LangSmith.
4. Add explicit tracing around retrieval and pipeline boundaries.
5. Reassess whether a broader provider abstraction is worth the extra complexity.

## Open Question To Confirm Before Coding

Should the first implementation scope stop at shared-client tracing for direct OpenAI calls, or should the first PR also include explicit top-level pipeline spans for retrieval and reranking?