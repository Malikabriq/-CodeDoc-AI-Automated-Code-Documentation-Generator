# `app/main.py` – Application Entry Point Documentation

---

## 1. Module Purpose

| Aspect | Description |
|--------|-------------|
| **Responsibility** | Instantiates the FastAPI application, registers the central API router, and exposes a simple health‑check endpoint (`/`). |
| **Why It Exists** | Serves as the canonical entry point for the **Task Management System API**. It centralises configuration (title, description, version) and ensures that all route definitions from `app.routes` are attached to the FastAPI app before the server starts. This makes the module the single source of truth for application boot‑strapping. |

---

## 2. Key Components

### 2.1. Imported Symbols

| Import | Origin | Reason |
|--------|--------|--------|
| `FastAPI` | `fastapi` (external library) | Provides the ASGI application class used to define the API. |
| `router` | `app.routes` (internal module) | The **APIRouter** instance that aggregates all endpoint definitions for tasks, users, etc. |

### 2.2. `app` – FastAPI instance  

```python
app = FastAPI(
    title="Task Management System API",
    description="API for managing tasks",
    version="1.0"
)
```

| Aspect | Details |
|--------|---------|
| **What it does** | Creates the main FastAPI application object, pre‑populated with OpenAPI metadata (title, description, version). |
| **Inputs** | Keyword arguments: <br>• `title` (str) – Human‑readable API name. <br>• `description` (str) – Short description displayed in the Swagger UI. <br>• `version` (str) – API version string. |
| **Outputs** | An instance of `fastapi.FastAPI` ready to have routes attached and to be served by an ASGI server (e.g., Uvicorn). |
| **Public API** | The `app` object is imported by the ASGI server entry point (`uvicorn app.main:app`) to start the service. |

### 2.3. Router registration  

```python
app.include_router(router)
```

| Aspect | Details |
|--------|---------|
| **What it does** | Mounts the external `router` (an `APIRouter`) onto the root path of the FastAPI app, making all its endpoints available. |
| **Inputs** | `router` – an `APIRouter` instance defined in `app.routes`. |
| **Outputs** | Routes from the router become part of `app.routes`. No value is returned. |
| **Public API** | None directly; this is internal wiring that makes the router’s endpoints publicly reachable. |

### 2.4. Root endpoint (`/`)  

```python
@app.get("/")
def root():
    return {"message": "Task Manager API is running!"}
```

| Aspect | Details |
|--------|---------|
| **What it does** | Provides a simple GET endpoint at the root URL that returns a JSON‑encoded health‑check message. |
| **Inputs** | No request parameters; FastAPI injects the request context automatically. |
| **Outputs** | `dict` → `{"message": "Task Manager API is running!"}` which FastAPI serialises to JSON. |
| **Public API** | Exposed to any HTTP client via `GET /`. Useful for uptime monitoring or quick sanity checks. |

---

## 3. Dependencies & Relationships

### 3.1. Imports

| Module | Imported Symbol(s) | Type |
|--------|--------------------|------|
| `fastapi` | `FastAPI` | External class (ASGI framework) |
| `app.routes` | `router` | Internal `APIRouter` instance (presumed defined as `router = APIRouter()` with task‑related endpoints) |

### 3.2. Interaction with Other Project Components

| Direction | Component | Interaction |
|-----------|-----------|-------------|
| **Depends on** | `app.routes` | Imports `router` to bind its routes to the main app. The router likely contains CRUD endpoints for task resources. |
| **Depends on** | FastAPI framework | Provides the core web server functionality. |
| **Depended on by** | ASGI server (e.g., `uvicorn`) | The server imports `app` from this module (`uvicorn app.main:app`) to launch the service. |
| **Depended on by** | Integration tests / client code | Tests reference the `app` object (via `TestClient(app)`) to exercise the API without starting a real server. |
| **Depended on by** | Optional external scripts (e.g., migrations) that import `app` for configuration discovery (OpenAPI generation). |

### 3.3. Architectural Fit

- **Layer:** *Presentation / API layer* – This file lives at the outermost edge of the system, exposing HTTP endpoints.
- **Responsibility:** *Bootstrapping* – Centralises startup configuration, analogous to a `main` function in other languages.
- **Relation to Domain Logic:** The heavy lifting (task creation, retrieval, etc.) resides in route handlers within `app.routes` and underlying service/repository layers. `app/main.py` merely wires those handlers into a runnable service.

---

## 4. Workflow Description

1. **Module import** – When Python imports `app.main`, the statements are executed in top‑down order.
2. **FastAPI instance creation** – `FastAPI(...)` constructs the ASGI application with the supplied metadata.
3. **Router inclusion** – `app.include_router(router)` registers all endpoints defined in `app.routes` under the root path (or a custom prefix if the router defines one).
4. **Root endpoint registration** – The decorator `@app.get("/")` registers the `root` function as a handler for GET requests to `/`.
5. **Export** – The module finishes loading, leaving the `app` object ready for an ASGI server (e.g., `uvicorn app.main:app`) to import and run.
6. **Runtime** – At request time, FastAPI matches incoming paths to the registered routes; for `/` it invokes `root()` and returns the JSON message.

**Call Flow Summary (request to `/`):**

```
HTTP GET /  ──► FastAPI router (app) 
                └─► matches path "/" → calls root()
                      → returns {"message": "..."}
                └─► FastAPI serialises dict → HTTP 200 JSON response
```

For any other route (e.g., `/tasks`), the flow is identical but the handler resides in `app.routes.router`.

---

## 5. Usage Examples

> **Note:** The only publicly usable object from this module is the `app` instance. The following examples assume the project is executed with **Uvicorn**.

### 5.1. Running the API locally

```bash
# From the project root (where the `app` package lives)
uvicorn app.main:app --reload
```

- `--reload` enables automatic reload on code changes (development mode).

### 5.2. Health‑check request (e.g., via `curl`)

```bash
curl http://127.0.0.1:8000/
# Expected JSON response:
# {"message":"Task Manager API is running!"}
```

### 5.3. Using FastAPI’s TestClient (unit testing)

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Task Manager API is running!"}
```

---

## 6. Notes for Developers

| Area | Guidance / Gotchas |
|------|--------------------|
| **Adding New Routes** | Define them in `app.routes` (or a dedicated sub‑router) and ensure the router is imported here. No further changes to `main.py` are required unless you need a different prefix or additional middleware. |
| **Middleware / Event Handlers** | If you need global middleware (e.g., CORS, authentication), add them *before* `app.include_router(router)` to guarantee they wrap all routes. |
| **Versioning** | The `version` argument is static in this file. For a more dynamic approach (e.g., reading from `pyproject.toml`), replace the hard‑coded string with a runtime read. |
| **Testing** | Import `app` directly from `app.main` for integration tests; avoid starting a real server. |
| **Circular Imports** | Ensure `app.routes` does **not** import `app.main` (directly or indirectly). If it needs the `app` instance, refactor shared utilities into a third module to avoid circular dependencies. |
| **Deployment** | In production, run the ASGI server (Uvicorn, Hypercorn, Gunicorn with Uvicorn workers) pointing at `app.main:app`. Keep `--reload` off and configure proper logging / workers. |
| **Extensibility** | For multiple API versions or micro‑services, consider splitting routers into separate modules and mounting them with prefixes (e.g., `app.include_router(v1_router, prefix="/v1")`). |

--- 

*End of documentation for `app/main.py`.*