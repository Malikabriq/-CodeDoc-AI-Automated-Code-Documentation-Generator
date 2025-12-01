# `setup_env.py` – Environment Variable Bootstrapper  

---  

## 1. Module Purpose  

| Aspect | Description |
|--------|-------------|
| **Responsibility** | Guarantees that three critical environment variables – `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, and `GITHUB_REPOSITORY` – are defined before the rest of the application runs. If any of them are missing, the module interactively prompts the user (concealing input for secret values) and injects the supplied values into the current process environment. |
| **Why it exists** | Many downstream components (e.g., GitHub App authentication, repository‑specific logic, CI pipelines) rely on these variables being present. Rather than failing with obscure `KeyError`s later, this script centralises the validation and acquisition of the required secrets, improving developer ergonomics and reducing runtime errors during local development, CI, or ad‑hoc scripts. |

---

## 2. Key Components  

The file contains **no functions or classes** – it consists of a single top‑level executable block. The block can be regarded as a *module‑level script* that runs automatically on import.

| Component | What it does | Inputs | Outputs / Side‑effects | Public API |
|-----------|--------------|--------|------------------------|------------|
| **Import statements** | Pull in the standard library modules `getpass` (secure prompt) and `os` (environment access). | – | – | – |
| **`env_var` loop** | Iterates over a predefined list of required environment variable names, checks each one, and if missing, asks the user to provide a value. The value is then stored in `os.environ`. | - List of strings (`["GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_REPOSITORY"]`) – hard‑coded.<br>- Current process environment (`os.getenv`). | - Populated `os.environ` entries for any missing variables.<br>- Interactive prompt on `stdin` (masked for security). | None – the side‑effect is the only “return value”. Importing this module runs the logic automatically. |

### Internal Logic Overview (loop)

```python
for env_var in ["GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_REPOSITORY"]:
    if not os.getenv(env_var):
        os.environ[env_var] = getpass.getpass(env_var + ": ")
```

1. **Iteration** – The loop covers each required key.  
2. **Presence check** – `os.getenv(env_var)` returns `None` (or empty string) if the variable is unset. The `not` guard triggers the prompt only when the variable is missing.  
3. **Prompt** – `getpass.getpass` prints `"<NAME>: "` and reads from the controlling terminal, hiding the user’s typing (useful for secrets).  
4. **Injection** – The received string is stored back into `os.environ`, making it instantly available to any subsequently imported module or code executed in the same process.  

---

## 3. Dependencies & Relationships  

### Imports
| Module | Reason for import |
|--------|-------------------|
| `getpass` | Provides `getpass(prompt)` for secure, non‑echoed user input. |
| `os` | Accesses and modifies the process environment via `os.getenv` and `os.environ`. |

### Interaction with the rest of the project  

| Direction | Component | Explanation |
|-----------|-----------|-------------|
| **Depends on** | Nothing external beyond the Python standard library. |
| **Potential dependents** | Any module that imports `setup_env` **before** it accesses the three environment variables. Typical candidates: <br>• GitHub API wrappers that need `GITHUB_APP_ID` & `GITHUB_APP_PRIVATE_KEY`. <br>• CI/CD scripts that need `GITHUB_REPOSITORY`. |
| **Placement in architecture** | Acts as an **initialisation guard**. In a typical entry‑point (`main.py`, test harness, CI job script) you would import this module first, ensuring the required configuration is present for downstream services. Because the code executes on import, developers must be aware that importing it triggers interactive I/O. |

---

## 4. Workflow Description  

1. **Module import** – As soon as Python evaluates `import setup_env`, the top‑level code runs.  
2. **Iterate over required keys** – The loop processes each of the three environment variable names in order.  
3. **Check existence** – For each variable, `os.getenv` is called.  
   - **If defined** – Skip to the next variable (no I/O).  
   - **If undefined** – Prompt the user using `getpass.getpass("<NAME>: ")`.  
4. **Store the value** – The user‑supplied string is placed into `os.environ[<NAME>]`. This updates the environment for the *current* Python process only.  
5. **Completion** – After the loop finishes, the module finishes importing. The environment is now guaranteed to contain values for all three keys, and execution continues with whichever code imported it.

*Call‑flow summary*  

```
import setup_env
   └─ for env_var in REQUIRED_VARS
          ├─ os.getenv(env_var)  →  None?
          ├─ Yes → getpass.getpass(prompt)
          └─ os.environ[env_var] = <user input>
```

---

## 5. Usage Examples  

The module does not expose a callable API, but its intended usage pattern is illustrated below.

```python
# main.py (or any entry point)
import setup_env      # Guarantees required vars are present

# At this point the three env vars are defined, either from the OS
# or from the interactive prompts that ran during import.
import my_github_client

client = my_github_client.GitHubAppClient(
    app_id=os.getenv("GITHUB_APP_ID"),
    private_key=os.getenv("GITHUB_APP_PRIVATE_KEY"),
    repository=os.getenv("GITHUB_REPOSITORY"),
)

# Continue with normal workflow...
```

*When running `python main.py` locally and any of the three variables are unset, the terminal will display:*

```
GITHUB_APP_ID: ********
GITHUB_APP_PRIVATE_KEY: ********
GITHUB_REPOSITORY: myorg/myrepo
```

(The first two inputs are masked thanks to `getpass`.)

---

## 6. Notes for Developers  

| Topic | Detail |
|-------|--------|
| **Side‑effects on import** | Importing this module triggers I/O. In non‑interactive contexts (e.g., automated CI pipelines) the prompts will block and eventually cause a failure if the required environment variables are not already set. Ensure the CI environment defines them, or guard the import with a check for `sys.stdin.isatty()`. |
| **Security** | `getpass` hides user typing, making it suitable for secret values like the private key. However, the secret is stored **in plain text** in the process environment (`os.environ`). Subsequent subprocesses inherit this value unless explicitly sanitized. |
| **Idempotence** | The logic only prompts when a variable is missing, so re‑importing the module in the same process does not re‑prompt. |
| **Extensibility** | Adding new required variables is as simple as appending them to the list. If more complex validation (e.g., format checking) is required, replace the loop with a helper function that raises descriptive errors. |
| **Testing** | Unit‑testing this module can be tricky because of the interactive prompt. Typical strategies:<br>• Monkey‑patch `os.getenv` and `getpass.getpass` to simulate missing variables and user input.<br>• Use `unittest.mock.patch.dict` to manipulate `os.environ` for each test case. |
| **Alternative designs** | For large projects you might prefer a dedicated configuration loader (e.g., using `python‑dotenv` or `pydantic-settings`). This module is intentionally lightweight and avoids third‑party dependencies, which is useful for quick scripts or minimal CI environments. |

---  

*End of documentation for `setup_env.py`.*