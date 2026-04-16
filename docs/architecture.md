# Application Architecture

## Project Structure Overview

This application follows a Flask blueprint pattern with clear separation between view rendering and API endpoints.

```
app/
├── main/          # View layer - HTML rendering
├── api/           # Data layer - JSON API endpoints
├── agents/        # Agent implementations
└── templates/     # Jinja2 HTML templates
```

## Routing Organization

### Main Routes (`app/main/routes.py`)
**Purpose**: Serve HTML pages (view layer)

```python
@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
def index():
    return render_template("index.html", messages=[])
```

These routes are responsible for:
- Rendering HTML templates
- Serving static pages
- Traditional server-side rendering

### API Routes (`app/api/api_selectors.py`)
**Purpose**: Serve JSON data endpoints (data layer)

```python
@bp.route("/api/select-agent", methods=["POST"])
def select_agent_route():
    # Returns JSON response
    
@bp.route("/api/chat", methods=["POST"])
def chat_route():
    # Returns JSON response
```

These routes are responsible for:
- Processing AJAX/fetch requests from the frontend
- Returning JSON responses
- Handling business logic for agent selection and chat

## Why Separate `api/` from `main/`?

### ✅ Benefits of Current Structure

1. **Separation of Concerns**
   - `main/`: HTML rendering (view layer)
   - `api/`: Data services (API layer)
   - Clear distinction between presentation and data

2. **RESTful Convention**
   - `/api/*` prefix clearly indicates JSON endpoints
   - Developers immediately know these routes return data, not HTML

3. **Scalability**
   - Easy to add new API endpoints without cluttering view routes
   - API can be versioned independently (`/api/v2/...`)
   - Can add authentication/rate limiting to API routes separately

4. **Frontend Independence**
   - API can serve multiple frontends: web, mobile, desktop
   - Frontend framework can change (React, Vue) without touching API
   - Enables SPA (Single Page Application) architecture

5. **URL Clarity & Documentation**
   - `/api/select-agent` tells developers "this returns JSON"
   - Auto-generated API docs can target `/api/*` routes
   - Testing frameworks can easily mock API layer

### ❌ Why NOT to Merge into `main/routes.py`

- Mixes view rendering with data API (violates single responsibility)
- Harder to maintain as application grows
- Difficult to apply middleware selectively (e.g., API-only auth)
- Confusing for new developers joining the project

## Request Flow: User Input → API → Response

### Frontend to Backend Flow

1. **User submits message** (`index.html`)
   ```javascript
   chatForm.addEventListener('submit', async function(e) {
       const text = messageInput.value.trim();
       addMessage(text, true);  // Render user message
   ```

2. **Call Agent Selector API**
   ```javascript
   const selectorResponse = await fetch('/api/select-agent', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ messages })
   });
   ```

3. **`select_agent_route()` handles request** (`api/api_selectors.py`)
   ```python
   def select_agent_route():
       body = request.get_json(silent=True) or {}
       messages = body.get("messages", [])
   ```

4. **Message Normalization** (lines 74-81)
   ```python
   normalized_messages: list[Message] = []
   for message in messages:
       role = message.get("role")
       content = message.get("content")
       # Validate role is 'user', 'assistant', or 'system'
       if role in {"user", "assistant", "system"} and isinstance(content, str):
           normalized_messages.append({"role": role, "content": content})
   ```
   
   **Why normalize?**
   - Security: Prevent malicious role injection
   - Validation: Ensure data integrity before processing
   - Type safety: Guarantee expected structure for downstream functions

5. **Agent Selection** (line 86)
   ```python
   agent, query = select_agent(normalized_messages)
   ```
   
   The `select_agent()` helper:
   - Analyzes recent conversation (last 5 messages)
   - Uses OpenAI to determine intent
   - Returns appropriate agent (`linkedin` or `rag`) and cleaned query

6. **Call Chat API** (`index.html`)
   ```javascript
   const chatResponse = await fetch('/api/chat', {
       method: 'POST',
       body: JSON.stringify({
           messages,
           agent: selectorData.agent,
           query: selectorData.query
       })
   });
   ```

7. **`chat_route()` executes selected agent** (`api/api_selectors.py`)
   ```python
   agent_executor = get_agent(agent)
   result = agent_executor(request_obj)
   return jsonify({
       "agent": result.agent,
       "response": result.content,
       "context": result.context or []
   })
   ```

8. **Display response** (`index.html`)
   ```javascript
   const agentLabel = chatData.agent === 'linkedin' 
       ? 'LinkedIn Agent' 
       : 'RAG Agent';
   addMessage(chatData.response, false, agentLabel);
   ```

## Key Architectural Decisions

### Blueprint Registration
Both blueprints are registered in `app/__init__.py`:
```python
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
```

### Agent Pattern
- **Registry**: `app/agents/registry.py` maintains available agents
- **Configuration**: `app/agents/agent_config.py` defines agent descriptions
- **Types**: `app/agents/agent_types.py` provides type safety with Pydantic

### Error Handling
Both API routes return consistent error responses:
```python
return jsonify({"error": "description"}), status_code
```

## Testing Implications

This structure enables:
- **Unit testing**: Test `select_agent()` helper independently
- **Integration testing**: Mock API endpoints for frontend tests
- **API testing**: Test API routes without touching HTML templates
- **E2E testing**: Full flow from frontend to backend

## Future Considerations

### API Versioning
```
/api/v1/select-agent
/api/v2/select-agent
```

### Authentication
Can apply decorators to all `/api/*` routes:
```python
@api_bp.before_request
def require_api_key():
    # Validate API key for all API routes
```

### Rate Limiting
Apply to API blueprint only, not main routes

### OpenAPI/Swagger Documentation
Can auto-generate docs from `/api/*` routes
