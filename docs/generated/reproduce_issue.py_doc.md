# `reproduce_issue.py` – Developer Documentation  

---

## 1. Module Purpose  

| Aspect | Description |
|--------|-------------|
| **Responsibility** | Dynamically loads the main application module (`app.py`), extracts the `fetch_pr_files` function, and executes it for a hard‑coded pull‑request identifier (`"2"`). The script prints the retrieved file list or a full traceback on failure. |
| **Why it exists** | Acts as a minimal, reproducible entry point for debugging or CI checks. By exercising the `fetch_pr_files` API in isolation, developers can quickly confirm whether a particular PR‑related bug is still present, without running the full application. |

---

## 2. Key Components  

| Component | Description |
|-----------|--------------|
| **Imports** | `import importlib.util`, `import sys`, `import os`, `from dotenv import load_dotenv`, `import traceback` |
| **Environment loading** <br>`load_dotenv()` | Reads a `.env` file (if present) and populates `os.environ`. This ensures any configuration needed by `app.py` (e.g., API tokens) is available before it is imported. |
| **Dynamic module loader** <br>`spec = importlib.util.spec_from_file_location("app_module", "app.py")`<br>`app_module = importlib.util.module_from_spec(spec)`<br>`sys.modules["app_module"] = app_module`<br>`spec.loader.exec_module(app_module)` | Loads `app.py` as a module named **app_module** without relying on the package import system. This technique works even when the repository root is not on `PYTHONPATH`. The loaded module is also registered in `sys.modules` so that subsequent imports of `app_module` resolve to this instance. |
| **Function extraction** <br>`fetch_pr_files = app_module.fetch_pr_files` | Retrieves the concrete implementation of `fetch_pr_files` from the freshly‑loaded `app_module`. No wrapper or aliasing is applied; the reference points directly at the original function object. |
| **Main execution block** | ```python\nprint("Attempting to fetch PR files for PR #2...")\ntry:\n    files = fetch_pr_files("2")\n    print(f\"Found {len(files)} files.\")\n    for f in files:\n        print(f\"File: {f['file']}\")\nexcept Exception as e:\n    traceback.print_exc()\n```<br>* **Inputs** – The PR identifier is the string `"2"` (hard‑coded).<br>* **Outputs** – On success: prints the number of returned file descriptors and each file name. On failure: prints the full traceback to standard output. |
| **Public API** | The script does **not** expose a reusable Python API; its only public effect is the side‑effect of executing the block when the file is run as a script (`python reproduce_issue.py`). |

---

## 3. Dependencies & Relationships  

### 3.1 Imports  

| Module | Reason for Import |
|--------|-------------------|
| `importlib.util` | Provides low‑level utilities (`spec_from_file_location`, `module_from_spec`) for dynamic module loading. |
| `sys` | Allows insertion of the loaded module into `sys.modules`. |
| `os` | Used indirectly by `dotenv.load_dotenv()` to access environment variables. |
| `dotenv.load_dotenv` | Reads a `.env` file so that any secrets or configuration required by `app.py` are available. |
| `traceback` | Prints a detailed exception traceback if `fetch_pr_files` raises. |

### 3.2 Interaction with Other Project Files  

| Direction | Component | Relationship |
|-----------|-----------|--------------|
| **Depends on** | `app.py` | The script loads `app.py` at runtime and accesses its `fetch_pr_files` function. All logic for PR file retrieval lives in `app.py`. |
| **Depends on (runtime)** | `.env` (optional) | Environment variables defined here may be required by `app.py` (e.g., GitHub token, database URL). |
| **Potential dependents** | Test harnesses, CI pipelines, debugging scripts | Any external script that wants to quickly verify the behavior of `fetch_pr_files` could import or execute `reproduce_issue.py`. |
| **Overall architecture** | `reproduce_issue.py` serves as a *thin façade* for `app.py`. It isolates the `fetch_pr_files` call, making it easy to reproduce an issue without launching the whole service (web server, background workers, etc.). |

---

## 4. Workflow Description  

1. **Environment preparation** – `load_dotenv()` populates `os.environ` from a `.env` file (if present).  
2. **Dynamic import** –  
   * Create a `ModuleSpec` for `"app_module"` pointing at `app.py`.  
   * Build a new module object from the spec.  
   * Register the module in `sys.modules` under the name `"app_module"` (so any subsequent imports resolve to this instance).  
   * Execute the module’s code (`spec.loader.exec_module`) – this runs `app.py` as if it were imported normally, defining its top‑level symbols (including `fetch_pr_files`).  
3. **Function extraction** – Grab the `fetch_pr_files` attribute from the imported module and bind it locally.  
4. **Invocation & reporting** –  
   * Print a pre‑flight message.  
   * Call `fetch_pr_files("2")`.  
   * On success: print the number of files and each file name (`f['file']`).  
   * On any exception: capture and display a full traceback via `traceback.print_exc()`.  

### Call Flow Summary  

```
reproduce_issue.py
│
├─ load_dotenv()                     ──► populates os.environ
│
├─ importlib.util.spec_from_file_location("app_module", "app.py")
│   └─> ModuleSpec
│
├─ importlib.util.module_from_spec(spec)
│   └─> empty module object (app_module)
│
├─ sys.modules["app_module"] = app_module
│
├─ spec.loader.exec_module(app_module)   ──► executes app.py
│   └─> defines fetch_pr_files in app_module
│
├─ fetch_pr_files = app_module.fetch_pr_files
│
└─ try:
       files = fetch_pr_files("2")
   └─> returns List[Dict] (each dict contains at least a "file" key)
       ├─ print number of files
       └─ loop → print each file name
   except Exception:
       traceback.print_exc()
```

---

## 5. Usage Examples  

The script is intended to be executed directly:

```bash
python reproduce_issue.py
```

**Expected console output (on success)**  

```
Attempting to fetch PR files for PR #2...
Found 3 files.
File: src/main.py
File: tests/test_main.py
File: README.md
```

**Expected console output (on failure)**  

```
Attempting to fetch PR files for PR #2...
Traceback (most recent call last):
  File ".../reproduce_issue.py", line 24, in <module>
    files = fetch_pr_files("2")
  File ".../app.py", line 57, in fetch_pr_files
    raise RuntimeError("Unable to contact GitHub")
RuntimeError: Unable to contact GitHub
```

*No additional API is exported; the script’s sole purpose is to run the above flow.*

---

## 6. Notes for Developers  

| Area | Guidance / Caveats |
|------|--------------------|
| **Hard‑coded PR identifier** | The script always queries PR `"2"`. Change the argument in the call to test other PRs. |
| **Dynamic import caveats** | Because `app.py` is executed via `exec_module`, any top‑level side effects (e.g., global configuration, logger setup) will run each time the script is launched. Ensure that `app.py` is idempotent or guard side effects if the script is used repeatedly in the same interpreter session. |
| **Environment variables** | Missing or incorrect entries in `.env` (or the environment) will cause failures inside `app.py` (e.g., authentication errors). Verify that required variables (commonly `GITHUB_TOKEN`, `GITHUB_REPO`) are present before running. |
| **Error handling** | The script deliberately prints the full traceback, which is useful for debugging but may expose secrets in logs. Consider sanitising or redirecting output in CI pipelines. |
| **Extensibility** | If additional functions from `app.py` need to be exercised, they can be added after the `fetch_pr_files` extraction (e.g., `some_other = app_module.some_other`). Keep the import logic unchanged. |
| **Testing** | For automated tests, it may be preferable to import `fetch_pr_files` directly from `app` (e.g., `from app import fetch_pr_files`). This script’s dynamic import is chiefly for isolated manual reproduction. |
| **Python version** | The script uses `importlib.util.spec_from_file_location`, which is available in Python 3.5+. Ensure the runtime matches the project's supported version. |

--- 

*End of documentation.*