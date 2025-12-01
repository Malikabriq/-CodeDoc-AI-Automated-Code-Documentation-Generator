# 📄 `app/utils/file_utils.py` – Developer Documentation  

---

## 1. Module Purpose
| Aspect | Description |
|--------|-------------|
| **Responsibility** | Provides a tiny persistence layer for the application’s **task data** by reading from and writing to a JSON file. |
| **Why it exists** | The rest of the code base works with an in‑memory representation of tasks (likely a `dict`). Centralising file I/O in this module isolates filesystem concerns (path handling, creation of missing directories, JSON serialization) from business logic, making the code easier to test and evolve. |

---

## 2. Key Components  

| Component | What it does | Signature | Inputs | Outputs | Internal Logic Overview | Public API |
|-----------|--------------|-----------|--------|---------|------------------------|------------|
| `DATA_FILE` (module‑level constant) | Absolute path to the JSON file that stores tasks. Constructed relative to this file: `<project_root>/data/tasks.json`. | `str` | *None* | *None* | Uses `os.path.join`, `os.path.dirname(__file__)` and `..` to step out of `app/utils` into the project root, then into the `data` folder. | **Read‑only constant** – can be imported by callers that need the exact path. |
| `load_data()` | Guarantees that the tasks file exists, then loads and returns its JSON contents as a Python object. | `def load_data() -> dict` | *None* | `dict` (the deserialized JSON) | 1. Checks `os.path.exists(DATA_FILE)`. <br>2. If missing, creates the parent directory (`os.makedirs(..., exist_ok=True)`) and writes an empty JSON object `{}` to the file. <br>3. Opens the file in text mode (`"r"`), UTF‑8 encoded, and runs `json.load`. | Exposed as a **read** operation for the whole data store. |
| `save_data(data)` | Persists the supplied Python object to the JSON file, overwriting any existing content. | `def save_data(data: dict) -> None` | `data: dict` – the in‑memory tasks representation to be stored. | `None` (writes to disk) | 1. Ensures the containing directory exists (`os.makedirs(..., exist_ok=True)`). <br>2. Opens `DATA_FILE` for writing (`"w"`), UTF‑8 encoded, and serialises `data` with `json.dump(..., indent=4)`. | Exposed as a **write** operation for the whole data store. |

*There are no classes or other functions in this file.*

---

## 3. Dependencies & Relationships  

### Imports
| Import | Reason |
|--------|--------|
| `os` | Path manipulation, existence checks, directory creation. |
| `json` | Serialization and deserialization of the tasks payload. |

### Interaction with Other Project Parts  

| Direction | Component | Nature of Interaction |
|-----------|-----------|-----------------------|
| **Depends on** | *Filesystem* (any OS that supports the standard `os` module) | Reads/writes `tasks.json`. |
| **Depends on** | *Calling code* (e.g., task‑management services, CLI commands, API handlers) | Calls `load_data()` to obtain the current task state and `save_data()` after modifications. |
| **Potential Dependents** | Modules that need persistent storage, such as `app/services/task_service.py`, CLI command handlers (`app/cli/*`), or HTTP route handlers (`app/api/*`). | They import `load_data` / `save_data` to persist task objects. |
| **Fit in Architecture** | **Data Access Layer (DAL)** – a very lightweight DAL for a JSON‑backed store. It sits *under* business‑logic services and *above* the raw filesystem, providing a clean, synchronous API (`load_data`, `save_data`). |

---

## 4. Workflow Description  

### Load Flow (`load_data`)
1. **Existence Check** – `os.path.exists(DATA_FILE)`  
   *If the file does not exist*:  
   a. `os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)` creates the `data/` directory (no error if already present).  
   b. Opens the file in write mode and writes an empty JSON object `{}` using `json.dump`.  
2. **Read & Parse** – Opens the file in read mode (`"r"`) with UTF‑8 encoding.  
3. **Deserialization** – `json.load` converts the JSON content into a Python `dict`.  
4. **Return** – The resulting dictionary is returned to the caller.

### Save Flow (`save_data`)
1. **Ensure Directory** – Calls `os.makedirs` on the parent directory with `exist_ok=True`.  
2. **Open for Writing** – Opens `DATA_FILE` in write mode (`"w"`), UTF‑8 encoding.  
3. **Serialization** – `json.dump(data, f, indent=4)` writes the supplied dictionary to disk, pretty‑printed with 4‑space indentation.  
4. **Completion** – Function returns `None`; the file now reflects the current in‑memory state.

Both functions are **synchronous** and block until the OS operation completes.

---

## 5. Usage Examples  

```python
# Example: Updating a task list
from app.utils.file_utils import load_data, save_data

# 1. Load the current tasks (dictionary)
tasks = load_data()          # → {}

# 2. Manipulate the in‑memory representation
tasks["todo"] = [
    {"id": 1, "title": "Write docs", "completed": False},
    {"id": 2, "title": "Implement feature X", "completed": False},
]

# 3. Persist the changes
save_data(tasks)
```

```python
# Example: Reading tasks in a CLI command
import click
from app.utils.file_utils import load_data

@click.command()
def list_tasks():
    data = load_data()
    for category, items in data.items():
        click.echo(f"{category}:")
        for task in items:
            status = "✅" if task.get("completed") else "❌"
            click.echo(f"  {status} [{task['id']}] {task['title']}")
```

---

## 6. Notes for Developers  

| Topic | Details |
|-------|---------|
| **File Location Assumption** | `DATA_FILE` is resolved relative to this module (`../data/tasks.json`). Changing the package layout requires updating the constant accordingly. |
| **Initial File Creation** | On the very first call to `load_data`, an empty JSON object is created. Callers should be prepared for an empty dict (`{}`) as the initial state. |
| **Thread‑Safety** | The functions are *not* thread‑safe. Concurrent calls may lead to race conditions or corrupted JSON. If the application will use multiple threads/processes, consider adding file locks or moving to a proper DB. |
| **Error Handling** | No explicit try/except blocks – any I/O or JSON errors propagate to the caller. This is intentional to surface serious failures (e.g., permission errors, malformed JSON). Callers should catch `OSError`, `json.JSONDecodeError`, etc., if they need graceful degradation. |
| **Data Size** | As the whole file is read/written each call, it works well for modest data sets (a few kilobytes). Large task collections would degrade performance; a more scalable storage (SQLite, NoSQL) would be advisable. |
| **Encoding** | Files are always read/written using UTF‑8. This matches most modern environments but be aware if the surrounding infrastructure expects a different encoding. |
| **Extensibility** | If a future feature requires partial updates (e.g., only one task), consider adding helper functions that load-modify-save internally, or refactor to a class that caches the in‑memory representation. |
| **Testing** | Because the module touches the real filesystem, tests should use temporary directories (`tempfile.TemporaryDirectory`) and monkey‑patch `DATA_FILE` or the `os.path` helpers to avoid polluting the production `data/` folder. |

--- 

*End of documentation for `app/utils/file_utils.py`.*