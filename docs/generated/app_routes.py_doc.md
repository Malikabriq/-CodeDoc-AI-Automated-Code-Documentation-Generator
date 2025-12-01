# 📘 `app/routes.py` – API Router Documentation

## 1. Module Purpose
| Why it exists | What it does |
|---------------|--------------|
| **Entry point for HTTP operations** | Defines a FastAPI `APIRouter` that groups all REST‑style endpoints related to task management. |
| **Separation of concerns** | Keeps request‑handling logic separate from data models (`app.models`) and persistence utilities (`app.utils.file_utils`). |
| **Reusability** | The `router` object can be included in the main FastAPI application (`app/main.py` or equivalent) with a single `include_router()` call. |

In short, this file implements the **public API** of the *Task Management System* – creating, reading, updating, deleting, and sorting tasks stored in a JSON‑backed data store.

---

## 2. Key Components

### 2.1 Router Instance
```python
router = APIRouter()
```
- **Type**: `fastapi.APIRouter`
- **Purpose**: Holds all route definitions; later attached to a FastAPI app.

---

### 2.2 End‑point Functions  

| Route | HTTP Method | Function | Synopsis | Input (type) | Output (type) | Notes |
|-------|-------------|----------|----------|--------------|---------------|-------|
| `/` | `GET` | `read_root` | Health‑check / welcome message | *none* | `dict[str, str]` | Returns static JSON. |
| `/about` | `GET` | `read_about` | Brief description of the API | *none* | `dict[str, str]` | Returns static JSON. |
| `/tasks` | `GET` | `view_all_tasks` | Retrieve the complete task collection | *none* | `dict[str, Any]` (as loaded from JSON) | Delegates to `load_data()`. |
| `/task/{task_id}` | `GET` | `view_task` | Fetch a single task by its identifier | `task_id: str` (path) | `dict[str, Any]` | Raises **404** if not found. |
| `/sort` | `GET` | `sort_tasks` | Return tasks sorted by a numeric field | `sort_by: str` (query, mandatory) <br> `order: str = "asc"` (query) | `list[dict]` | Validates `sort_by` against `["estimated_hours","hours_spent","progress"]`. |
| `/create` | `POST` | `create_task` | Persist a new task | `task: Task` (pydantic model, body) | `JSONResponse` (201) | Fails with **400** if `id` already exists. |
| `/edit/{task_id}` | `PUT` | `update_task` | Partially update an existing task | `task_id: str` (path) <br> `task_update: TaskUpdate` (pydantic, body) | `JSONResponse` (200) | Merges `exclude_unset` fields; raises **404** when missing. |
| `/delete/{task_id}` | `DELETE` | `delete_task` | Remove a task | `task_id: str` (path) | `JSONResponse` (200) | Raises **404** when task does not exist. |

#### 2.2.1 `read_root()`
- **Logic**: Returns a constant greeting JSON.
- **Public API**: `GET /`

#### 2.2.2 `read_about()`
- **Logic**: Returns a static description JSON.
- **Public API**: `GET /about`

#### 2.2.3 `view_all_tasks()`
- **Logic**: Calls `load_data()` from `app.utils.file_utils` which reads the JSON file and returns a dictionary keyed by task IDs.
- **Public API**: `GET /tasks`

#### 2.2.4 `view_task(task_id)`
- **Logic**:  
  1. Load complete data.  
  2. Look up `task_id`.  
  3. Return the stored task dict or raise `HTTPException(404)`.
- **Parameters**: `task_id` uses FastAPI `Path` for OpenAPI metadata (description, example).

#### 2.2.5 `sort_tasks(sort_by, order)`
- **Logic**:  
  1. Validate `sort_by` against allowed fields.  
  2. Validate `order` (`asc`/`desc`).  
  3. Load all tasks.  
  4. Sort the list of task dicts by the chosen field, using `reverse = (order == "desc")`.  
  5. Return the sorted list.
- **Error handling**: `400 Bad Request` for invalid field or order.

#### 2.2.6 `create_task(task)`
- **Logic**:  
  1. Load current data.  
  2. Ensure `task.id` is unique.  
  3. Convert the `Task` Pydantic model to a plain dict **excluding** the `id` (the `id` is used as the key).  
  4. Persist via `save_data()`.  
  5. Respond with **201 Created** and a confirmation message.
- **Model**: `Task` comes from `app.models` and must contain at least an `id` attribute.

#### 2.2.7 `update_task(task_id, task_update)`
- **Logic**:  
  1. Load data; verify existence of `task_id`.  
  2. Extract the stored dict (`existing_task`).  
  3. Build a dict of fields provided in the request (`exclude_unset=True`).  
  4. Merge updates into `existing_task`.  
  5. Re‑instantiate a `Task` model to guarantee schema conformity.  
  6. Persist the merged dict (again, without the `id` key).  
  7. Return **200 OK** with a success message.
- **Partial updates**: Only fields present in the request body are altered.

#### 2.2.8 `delete_task(task_id)`
- **Logic**:  
  1. Load data; confirm task existence.  
  2. Remove the entry from the dict.  
  3. Persist the new dict.  
  4. Return **200 OK** with a confirmation message.

---

## 3. Dependencies & Relationships

| Imported Symbol | Origin | Role in this Module |
|-----------------|--------|---------------------|
| `APIRouter` | `fastapi` | Container for route definitions |
| `HTTPException` | `fastapi` | Standardized error responses (404, 400) |
| `Path`, `Query` | `fastapi` | Declarative request parameter validation & OpenAPI docs |
| `JSONResponse` | `fastapi.responses` | Custom response with explicit status code |
| `Task`, `TaskUpdate` | `app.models` | Pydantic models describing task schema (creation & patch) |
| `load_data`, `save_data` | `app.utils.file_utils` | JSON‑file persistence helpers |

### Interaction Diagram (high‑level)

```
[FastAPI Application] --> includes --> app.routes.router
app.routes.router --> uses --> app.models.Task / TaskUpdate
app.routes.router --> calls --> app.utils.file_utils.load_data / save_data
app.routes.router <-- receives HTTP requests (GET, POST, PUT, DELETE)
```

- **Components this file depends on**  
  - **Models** (`Task`, `TaskUpdate`) for validation and data shaping.  
  - **File utilities** (`load_data`, `save_data`) for persistence.

- **Components that likely depend on this file**  
  - The **main FastAPI app** (e.g., `app/main.py`) that registers the router.  
  - Automated **OpenAPI documentation** generated by FastAPI, which extracts path operations from this router.

- **Architectural fit**  
  - **Presentation layer** – Exposes a RESTful API.  
  - **Business logic** – Minimal; most logic lives inside route handlers and helper utilities.  
  - **Data access layer** – Abstracted via `load_data` / `save_data` (simple file‑based store).  

---

## 4. Workflow Description

1. **Application start‑up**  
   - FastAPI creates an instance of `APIRouter` (`router`).  
   - `router` is later registered with the main FastAPI app via `app.include_router(app.routes.router)`.

2. **Incoming HTTP request** hits one of the defined routes. FastAPI:
   - Parses URL path parameters (`task_id`) and query parameters (`sort_by`, `order`).  
   - Deserializes request bodies into the corresponding Pydantic models (`Task`, `TaskUpdate`).

3. **Handler execution** (e.g., `create_task`)  
   - Calls `load_data()` → reads the JSON file into a Python dict.  
   - Performs validation / business checks (e.g., uniqueness, existence).  
   - Mutates the in‑memory dict as needed.  
   - Calls `save_data(updated_dict)` → writes the updated dict back to the JSON file (overwrites the previous content).  
   - Returns a FastAPI response object (`JSONResponse` or plain dict).

4. **Error handling**  
   - When validation fails, a `HTTPException` is raised; FastAPI translates it into a proper JSON error payload with the given status code.

5. **Response**  
   - FastAPI serializes the returned Python object (dict, list, or `JSONResponse`) to JSON and sends it to the client.

---

## 5. Usage Examples  

> **Note**: The examples assume the FastAPI server runs locally on `http://localhost:8000`.

### 5.1 Simple `curl` commands

```bash
# 1️⃣ Check API health
curl -X GET http://localhost:8000/

# 2️⃣ List all tasks
curl -X GET http://localhost:8000/tasks

# 3️⃣ Get a single task (replace T001 with an actual ID)
curl -X GET http://localhost:8000/task/T001

# 4️⃣ Sort tasks by estimated_hours descending
curl -G http://localhost:8000/sort \
     --data-urlencode "sort_by=estimated_hours" \
     --data-urlencode "order=desc"

# 5️⃣ Create a new task (JSON body)
curl -X POST http://localhost:8000/create \
     -H "Content-Type: application/json" \
     -d '{
           "id": "T010",
           "title": "Write documentation",
           "description": "Prepare API docs",
           "estimated_hours": 5,
           "hours_spent": 0,
           "progress": 0
         }'

# 6️⃣ Partially update a task
curl -X PUT http://localhost:8000/edit/T010 \
     -H "Content-Type: application/json" \
     -d '{"hours_spent": 2, "progress": 40}'

# 7️⃣ Delete a task
curl -X DELETE http://localhost:8000/delete/T010
```

### 5.2 Python client using `httpx`

```python
import httpx

BASE = "http://localhost:8000"

# Create a task
new_task = {
    "id": "T011",
    "title": "Code review",
    "description": "Review PR #42",
    "estimated_hours": 2,
    "hours_spent": 0,
    "progress": 0,
}
resp = httpx.post(f"{BASE}/create", json=new_task)
print(resp.json())

# Get all tasks
resp = httpx.get(f"{BASE}/tasks")
print(resp.json())
```

---  

## 6. Notes for Developers  

| Area | Recommendation / Caveat |
|------|---------------------------|
| **Persistence** | `load_data` / `save_data` operate on a flat JSON file. This is **not thread‑safe** – concurrent requests may lead to race conditions or lost updates. Consider adding a file lock or moving to a proper database for production. |
| **Data Validation** | The heavy lifting is done by the Pydantic models (`Task`, `TaskUpdate`). Ensure these models enforce all required fields and proper types (e.g., non‑negative numbers). |
| **Error Messages** | The API currently returns generic 400/404 messages. For a public API, you may want to standardize error payloads (e.g., `{ "error": "...", "code": 400 }`). |
| **Sorting Implementation** | Sorting uses `dict.get(sort_by, 0)`. If a task lacks the field, it defaults to `0`, which may hide data‑quality issues. Consider validating field presence at model level. |
| **Response Consistency** | `view_*` endpoints return raw dict/list structures, while mutating endpoints return `JSONResponse` with a custom message. Align response schemas (e.g., always wrap in `{ "data": ..., "message": ... }`). |
| **Extensibility** | Adding pagination, filtering, or authentication will require changes mainly in this module (route definitions) and possibly in `load_data` to support query parameters. |
| **Testing** | Unit‑test each handler by mocking `load_data` / `save_data`. FastAPI’s `TestClient` provides an easy way to simulate HTTP requests. |
| **OpenAPI Docs** | Because path and query parameters are declared with `Path` and `Query`, the auto‑generated Swagger UI already shows examples and descriptions. Keep those docstrings up‑to‑date for best developer experience. |
| **Security** | No authentication / rate‑limiting is present. For a real deployment, wrap the router with dependencies that enforce JWT, API keys, or OAuth scopes. |
| **Future Refactor** | If the project grows, consider moving the CRUD logic to a **service layer** (e.g., `app.services.task_service`) so that route handlers stay thin and testable. |

---  

*End of documentation.*