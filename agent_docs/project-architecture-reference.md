# Project Architecture Reference

This document is a concise reference for the current application structure and execution paths relevant to LangSmith observability work.

## Application Shape

- The project is a Flask application using the app factory pattern.
- The Flask app is created in `app/__init__.py`.
- Routes are split across two blueprints:
  - `app/main` for HTML views
  - `app/api` for JSON and streaming endpoints

## Key Request Flow

The current chat flow is organized into two phases:

1. Agent selection
2. Agent execution

### Agent Selection

- Entry point: `app/api/api_selectors.py`
- Function: `select_agent(messages)`
- Behavior:
  - normalizes recent chat messages
  - calls OpenAI directly using `OpenAI(...)`
  - returns a selected agent type and refined query

This is currently part of the runtime path for every chat request.

### Agent Execution

- Entry points:
  - `chat_route()` in `app/api/api_selectors.py`
  - `chat_stream_route()` in `app/api/api_selectors.py`
- These routes:
  - build an `AgentRequest`
  - resolve the agent implementation through `app/agents/registry.py`
  - execute either the sync or streaming agent path

## Current Agent Types

### LinkedIn Agent

- File: `app/agents/linkedin.py`
- Purpose: generate LinkedIn-style content from the user request
- Current implementation:
  - builds a prompt from `AgentRequest`
  - uses direct `OpenAI(...)` chat completion calls
  - supports both sync and streaming execution

### RAG Agent

- File: `app/agents/registry.py`
- Purpose: retrieve relevant context and generate a grounded answer
- Current implementation:
  - generates embeddings for the refined query
  - queries Pinecone for candidate matches
  - reranks the retrieved documents
  - calls OpenAI chat completion to produce the final answer
  - supports both sync and streaming execution

## Retrieval Stack

### Embeddings

- Used in:
  - `app/agents/registry.py`
  - `app/main/index_pipeline.py`
- Implementation:
  - `langchain_openai.OpenAIEmbeddings(...)`

### Vector Search and Reranking

- File: `app/main/pinecone_client.py`
- Implementation:
  - wraps Pinecone query, fetch, upsert, and rerank operations

### Indexing Pipeline

- File: `app/main/index_pipeline.py`
- Purpose:
  - scrape source content
  - chunk documents
  - generate embeddings
  - upsert vectors into Pinecone

This pipeline is separate from request-time answer generation, but it shares the same embeddings dependency.

## Shared Contracts

- File: `app/agents/agent_types.py`
- Core types:
  - `AgentRequest`
  - `AgentResponse`
  - `StreamingAgentResponse`
  - `Message`
  - RAG context and source reference typed dicts

These types define the execution boundary between the HTTP layer and the agent implementations.

## Configuration Surface

- File: `config.py`
- Relevant settings include:
  - `OPENAI_API_KEY`
  - `BASE_MODEL`
  - `OPENAI_FINETUNED_MODEL`
  - `PINECONE_API_KEY`
  - `PINECONE_INDEX`
  - `PINECONE_NAMESPACE`
  - `RAG_INITIAL_FETCH`
  - `RAG_TOP_K`

LangSmith-related environment variables are also expected to live in this configuration surface.

## Observability-Relevant Boundaries

The most important boundaries for tracing are:

1. HTTP request entry in `app/api/api_selectors.py`
2. Agent selection in `select_agent(...)`
3. Retrieval and reranking in `app/agents/registry.py`
4. Final generation in `app/agents/registry.py` and `app/agents/linkedin.py`
5. Embedding generation in `app/agents/registry.py` and `app/main/index_pipeline.py`
6. Pinecone operations in `app/main/pinecone_client.py`

## Current Architectural Constraints

- Flask remains the application server.
- The existing route contracts should remain stable.
- The app currently orchestrates its own agent flow.
- The runtime does not currently use the OpenAI Agents SDK.
- OpenAI usage is split between:
  - direct `openai` client calls
  - LangChain OpenAI embeddings wrappers

## Why This Matters For LangSmith

- Direct OpenAI chat calls can be centralized behind a shared wrapped client.
- Embeddings and Pinecone operations are separate integration points and may need explicit tracing.
- The app already has clear execution boundaries, which makes incremental observability changes feasible without rewriting orchestration.