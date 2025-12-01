# `app/db.py` – Persistent JSON Storage Module  

---

## 1. Module Purpose  

**What this file is responsible for**  
- Provides a tiny, file‑based persistence layer for the application.  
- Guarantees that a `tasks.json` file exists inside the package’s `data` directory.  
- Exposes three small public functions (`ensure_data_dir`, `load_data`, `save_data`) that read from and write to that JSON document.

**Why it exists in the project**  
- The rest of the code base (e.g., task‑management routes, services, or CLI commands) needs a simple way to store and retrieve the current set of tasks without pulling in a full‑blown database.  
- By centralising file‑system handling in this module, the rest of the code can work with ordinary Python dictionaries while the module abstracts away path creation, file‑opening, and JSON (de)serialization.

---

## 2. Key Components  

| Symbol | Type | Description | Inputs / Outputs | Internal Logic Overview | Public API |
|--------|------|-------------|------------------|------------------------|------------|
| `DATA_FILE` | `str` (module constant) | Absolute path to `data/tasks.json` next to this file. Constructed with `os.path.join(os.path.dirname(__file__), "data", "tasks.json")`. | – | – | – |
| `ensure_data_dir()` | `None` | Guarantees that the `data` directory exists **and** that `tasks.json` exists (empty JSON object if missing). | No arguments, returns `None`. | 1. Derive the directory from `DATA_FILE`. <br>2. `os.makedirs(..., exist_ok=True)` creates it if necessary. <br>3. If the JSON file does not exist, open it for writing and dump `{}`. | **Yes** – called internally by `load_data`/`save_data`, and may be invoked manually to initialise the storage. |
| `load_data()` | `dict` | Reads the persisted JSON document and returns the deserialized Python object. | No arguments, returns a `dict` (or whatever JSON root object is stored; currently an empty dict is written on first run). | 1. Calls `ensure_data_dir()` to guarantee file existence. <br>2. Opens `DATA_FILE` in text read mode (`utf‑8`). <br>3. Returns `json.load(f)`. | **Yes** – callers obtain the current task data. |
| `save_data(data)` | `None` | Serialises *data* to JSON and overwrites `tasks.json`. | `data: Any` (must be JSON‑serialisable, usually a `dict`). Returns `None`. | 1. Calls `ensure_data_dir()` to guarantee the folder/file exists. <br>2. Opens `DATA_FILE` in write mode (`utf‑8`). <br>3. `json.dump(data, f, indent=4)` writes a pretty‑printed JSON document. | **Yes** – callers persist changes made to the in‑memory data structure. |

> **Note:** The module does **not** define any classes; its public API is the three functions above.

---

## 3. Dependencies & Relationships  

### Imports  

| Module | Reason |
|--------|--------|
| `os`   | Path manipulation (`os.path.dirname`, `os.path.join`) and directory creation (`os.makedirs`). |
| `json` | Serialize/deserialize the task data to/from the JSON file. |

### Interaction with Other Project Files  

- **Dependencies (what this module needs):**  
  - Only the Python standard library (`os`, `json`).  
  - The filesystem layout: it assumes a sibling `data/` directory is writable.

- **Dependents (what likely imports this module):**  
  - Any module dealing with task CRUD operations (e.g., `app/tasks.py`, API route handlers, command‑line utilities).  
  - Test suites that need to seed or inspect the persistent store.  

- **Architectural Fit:**  
  - Acts as the **persistence adapter** in a simple **Hexagonal / Clean Architecture**: the core domain uses plain Python objects, while this adapter translates them to a durable format.  
  - Because it is deliberately tiny, swapping it for a database or other storage backend can be done by replacing the implementation while keeping the same public function signatures.

---

## 4. Workflow Description  

1. **Module import** – Constants and functions are defined; no I/O occurs yet.  
2. **First access** – When `load_data()` or `save_data()` is called:  
   a. `ensure_data_dir()` runs.  
   b. It derives the directory (`data/`) from `DATA_FILE`.  
   c. `os.makedirs(..., exist_ok=True)` creates the directory if missing.  
   d. If `tasks.json` does not exist, it creates the file and writes `{}` (empty JSON object).  
3. **Loading** – `load_data()` opens `tasks.json` for reading and returns the parsed JSON (a `dict`).  
4. **Modifying** – Caller mutates the returned dictionary (e.g., adds, updates, deletes tasks).  
5. **Saving** – Caller passes the (now‑modified) dictionary to `save_data(data)`.  
   a. `ensure_data_dir()` runs again (harmless if the directory already exists).  
   b. The file is opened for writing, and the dictionary is encoded to pretty‑printed JSON (`indent=4`).  
6. **Subsequent calls** repeat steps 2‑5, always working against the same `tasks.json` file.

**Call Flow Summary**

```
load_data()  --> ensure_data_dir() --> (create dir/file if needed) --> json.load()
save_data(d) --> ensure_data_dir() --> (create dir/file if needed) --> json.dump(d)
```

---

## 5. Usage Examples  

```python
# Example: Retrieve current tasks, add a new one, and persist the change.

from app.db import load_data, save_data

# 1. Load the existing data (will be {} on first run)
tasks = load_data()          # type: dict

# 2. Manipulate the dict – add a new task
new_task_id = "task-001"
tasks[new_task_id] = {
    "title": "Write documentation",
    "completed": False,
    "created_at": "2025-12-01T12:34:56Z"
}

# 3. Persist the updated collection
save_data(tasks)
```

```python
# Example: Reset the storage (clears all tasks)
from app.db import save_data

save_data({})   # Overwrites tasks.json with an empty JSON object
```

---

## 6. Notes for Developers  

| Area | Detail |
|------|--------|
| **File‑system assumptions** | The module expects that the process has write permission to the package directory. If the app is packaged read‑only (e.g., inside a Docker image without a mounted volume), `ensure_data_dir()` will raise an `OSError`. |
| **Concurrent access** | No locking is performed. Simultaneous reads are fine, but concurrent writes (or a read‑while‑write) can corrupt the JSON file. If the project grows to multi‑process usage, consider file locks or moving to a real DB. |
| **Data validation** | `save_data` trusts the caller to provide JSON‑serialisable data. Passing non‑serialisable objects (e.g., `datetime` objects) will raise `TypeError`. Validation should happen upstream. |
| **Error handling** | All I/O errors bubble up as standard exceptions (`FileNotFoundError`, `JSONDecodeError`, `OSError`, etc.). Callers may want to catch these to provide user‑friendly messages. |
| **Extensibility** | To switch to another storage backend, replace the three public functions while keeping their signatures. The rest of the code base can remain unchanged. |
| **Testing** | Unit tests can monkey‑patch `DATA_FILE` to point to a temporary location, ensuring no side‑effects on real data. Use `tempfile` and clean up the temporary directory after each test. |
| **Encoding** | Files are always opened with UTF‑8, which matches the default for JSON and avoids locale‑dependent surprises. |
| **Formatting** | `json.dump(..., indent=4)` provides human‑readable output, useful when developers inspect `tasks.json` during debugging. |

--- 

*End of documentation for `app/db.py`.*