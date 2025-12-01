# `app/crud.py` – CRUD Operations for Task Entities  

---  

## 1. Module Purpose  

| Aspect | Description |
|--------|-------------|
| **Responsibility** | Provides a thin, functional **CRUD (Create, Read, Update, Delete)** layer for the `Task` domain model. All operations read from and write to the persistent JSON store through the `load_data` / `save_data` helpers. |
| **Why it exists** | Centralising data‑access logic in a single module keeps the rest of the code‑base (e.g., API routers, services, UI) free from low‑level file handling details. This module acts as the single source of truth for how tasks are persisted, validated, and mutated. |

---

## 2. Key Components  

The file contains **six functions** – each implements one of the CRUD actions plus a helper for bulk retrieval.

| Function | Purpose | Signature | Parameters | Return / Side‑effects | Internal Logic Highlights | Public API |
|----------|---------|-----------|------------|-----------------------|---------------------------|------------|
| `get_all` | Retrieve **all** stored tasks as a raw dictionary. | `def get_all():` | *none* | `dict[str, dict]` – mapping of *task_id* → serialized task data. | Calls `load_data()` and returns the dictionary unchanged. | ✔️ Exported |
| `get` | Retrieve a **single** task by its identifier. | `def get(task_id: str):` | `task_id: str` – key of the desired task. | `dict | None` – the stored representation of the task, or `None` if missing. | Loads full data, then `data.get(task_id)`. | ✔️ Exported |
| `create` | Persist a **new** `Task`. | `def create(task: Task):` | `task: Task` – Pydantic model instance (must have a unique `id`). | *None* (writes to storage). Raises `ValueError` if a task with the same `id` already exists. | 1. Load data. <br>2. Guard against duplicate IDs. <br>3. Serialize the model with `model_dump(exclude={"id"})` (ID is used as the key, not stored inside the value). <br>4. Save the updated dict. | ✔️ Exported |
| `update` | Apply **partial** updates to an existing task. | `def update(task_id: str, task_update: TaskUpdate):` | `task_id: str` – identifier of the task to modify.<br>`task_update: TaskUpdate` – Pydantic model containing only the fields to change (unset fields are ignored). | *None* (writes to storage). Raises `ValueError` if the target task does not exist. | 1. Load data.<br>2. Verify the task exists.<br>3. Extract the current stored dict (`existing_task`).<br>4. Produce a dict of provided fields via `task_update.model_dump(exclude_unset=True)`. <br>5. Merge each provided field into `existing_task`. <br>6. Re‑inject the `id` (ensures it stays correct). <br>7. Re‑instantiate a full `Task` object to validate the merged result.<br>8. Serialize the validated task (excluding `id`) back into the store.<br>9. Persist with `save_data`. | ✔️ Exported |
| `delete` | Remove a task permanently. | `def delete(task_id: str):` | `task_id: str` – identifier of the task to delete. | *None* (writes to storage). Raises `ValueError` if the task is missing. | 1. Load data.<br>2. Guard against missing key.<br>3. `del data[task_id]`.<br>4. Persist the new dict. | ✔️ Exported |

> **Note:** All functions rely on the **side‑effect** of `save_data` to persist changes. No function returns the newly saved object; callers must re‑fetch if they need the updated representation.

---

## 3. Dependencies & Relationships  

| Category | Items | Relationship |
|----------|-------|--------------|
| **Internal Imports** | `load_data`, `save_data` from `app.db` | *Read* and *write* the JSON storage file. |
| | `Task`, `TaskUpdate` from `app.models` | *Domain* models used for validation and (de)serialization. |
| **External / Standard Library** | None (the module only uses the above imports). |
| **Components this file depends on** | • `app.db.load_data` – returns `dict[str, dict]`.<br>• `app.db.save_data` – accepts the same dict and writes it to disk.<br>• `app.models.Task` – full task schema (including `id`).<br>• `app.models.TaskUpdate` – schema for partial updates with optional fields. |
| **Components that likely depend on this file** | • API routers (e.g., FastAPI Endpoints) that expose HTTP CRUD endpoints.<br>• Service layer or use‑case functions that orchestrate business logic.<br>• CLI utilities or background jobs that manipulate tasks programmatically. |
| **Architectural Position** | Sits in the **data‑access layer** of a typical clean‑architecture / hexagonal design: <br>`API → Service → CRUD (this module) → Persistence (db module)`. It isolates storage mechanics from higher‑level concerns. |

---

## 4. Workflow Description  

Below is a **step‑by‑step** flow for each operation, followed by an overall call‑graph summary.

### 4.1 `get_all()`

1. Invoke `load_data()` → reads the JSON file into a Python dict.  
2. Return the dict unchanged.

### 4.2 `get(task_id)`

1. Load the complete data with `load_data()`.  
2. Use dict `get` to retrieve the entry for `task_id`.  
3. Return the raw stored dict (or `None`).

### 4.3 `create(task)`

1. Load current storage.  
2. If `task.id` already a key → raise `ValueError`.  
3. Serialize `task` **without** the `id` field (`exclude={"id"}`) – the `id` is the dict key.  
4. Insert serialized dict into the loaded data under `task.id`.  
5. Call `save_data(updated_data)` to write the file.

### 4.4 `update(task_id, task_update)`

1. Load data.  
2. Verify `task_id` exists → otherwise raise `ValueError`.  
3. Grab the stored dict for the task (`existing_task`).  
4. Convert `task_update` to a dict **only** for fields that were actually supplied (`exclude_unset=True`).  
5. Overwrite/assign each supplied field on `existing_task`.  
6. Explicitly set `existing_task["id"] = task_id` to keep the identifier consistent.  
7. **Validate** the merged dict by constructing a new `Task(**existing_task)` – any schema violations raise a Pydantic error here.  
8. Serialize the validated task again (excluding `id`) and replace the entry in the data dict.  
9. Persist with `save_data`.

### 4.5 `delete(task_id)`

1. Load data.  
2. Ensure `task_id` exists → otherwise raise `ValueError`.  
3. Delete the key from the dict.  
4. Persist the modified dict.

### 4.6 Overall Call Flow  

```
┌─────────────────────┐
│  API / Service Layer │
└─────────┬───────────┘
          │ (calls)
          ▼
   ┌───────────────┐
   │  app/crud.py  │   ←───► load_data() (app/db)
   │   Functions   │   ◄───► save_data() (app/db)
   │ (CRUD ops)    │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │  app/models   │   (Task, TaskUpdate)
   └───────────────┘
```

---

## 5. Usage Examples  

> **Only the functions defined in this module are shown.**  
> These snippets assume the surrounding project has correctly configured `app.db` (e.g., a JSON file path) and that `Task` / `TaskUpdate` are Pydantic models with the expected fields.

### 5.1 Create a new task  

```python
from app.models import Task
from app.crud import create

new_task = Task(
    id="task-001",
    title="Write documentation",
    description="Create CRUD module docs",
    completed=False,
)

create(new_task)   # Persists the task; raises ValueError if id exists.
```

### 5.2 Retrieve a task  

```python
from app.crud import get

task_data = get("task-001")
if task_data:
    print("Task found:", task_data)
else:
    print("Task not found")
```

### 5.3 Update a task partially  

```python
from app.models import TaskUpdate
from app.crud import update

partial_update = TaskUpdate(completed=True)   # Only change 'completed' flag
update("task-001", partial_update)           # Raises ValueError if missing
```

### 5.4 Delete a task  

```python
from app.crud import delete

delete("task-001")   # Removes the entry; raises ValueError if not present
```

### 5.5 List all tasks  

```python
from app.crud import get_all

all_tasks = get_all()
print(f"{len(all_tasks)} tasks stored")
```

---

## 6. Notes for Developers  

| Area | Guidance / Gotchas |
|------|--------------------|
| **Data shape** | The storage format is a JSON object where each **key** is a task’s `id` and the **value** is the task’s fields **except** `id`. This convention is hard‑coded (`exclude={"id"}`) – deviating from it will break `create`/`update`. |
| **Atomicity** | Each CRUD call loads the full dataset, mutates it in memory, then writes the entire file back. This is simple but can cause race conditions in concurrent environments (e.g., multiple processes). Consider adding file‑locking or moving to a real database if concurrency becomes a requirement. |
| **Validation** | `create` stores the raw `model_dump` without re‑instantiating a `Task`. If the incoming `Task` instance is already validated (as Pydantic does on creation), this is safe. `update` **re‑validates** by building a new `Task` from the merged dict; any schema violation will raise a `pydantic.ValidationError`. |
| **Error handling** | The module uses `ValueError` for “not found” and “already exists” situations. Callers should catch these explicitly (or convert to HTTP 404/409 in an API layer). |
| **Extensibility** | Adding new fields to `Task` requires only updating the Pydantic model – the CRUD code automatically forwards the added keys because it works with generic dicts. |
| **Testing** | Because the functions depend on file I/O, unit tests should **mock** `load_data` and `save_data` to avoid disk side effects. Example: `unittest.mock.patch('app.crud.load_data', return_value={})`. |
| **Performance** | For very large task collections, loading the whole JSON file for each operation may become a bottleneck. If scaling is needed, replace `load_data`/`save_data` with a database driver and adjust the CRUD logic accordingly. |
| **Future enhancements** | • Introduce pagination for `get_all`.<br>• Add bulk‑create/update methods.<br>• Wrap the module in a class (e.g., `TaskRepository`) to allow dependency injection of the storage backend. |

---  

*End of documentation for `app/crud.py`.*