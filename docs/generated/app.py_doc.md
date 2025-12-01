# Documentation for `app.py`

---

## 1. Module Purpose

**What this file is responsible for**  
`app.py` is a utility script that automatically generates comprehensive developer documentation for source files in a codebase. It scans the repository for relevant source files, extracts their contents, sends them to an LLM (via the Ollama API) with a detailed prompt, receives Markdown‑formatted documentation, and stores the result in a generated‑docs directory.

**Why it exists in the project**  
Maintaining high‑quality documentation is often time‑consuming and easy to neglect. This module provides an automated, repeatable way to produce consistent, thorough documentation for every supported source file (`.py`, `.js`, `.ts`, `.java`, `.go`). By integrating with Ollama, it leverages a powerful language model to generate human‑readable docs without requiring manual authoring.

---

## 2. Key Components

| Component | Description | Signature / Type | Public API |
|-----------|-------------|------------------|------------|
| **Constants** | | | |
| `OLLAMA_MODEL` | The Ollama model identifier used for documentation generation. | `str` (`"gpt-oss:120b-cloud"`) | – |
| `SOURCE_EXTENSIONS` | Set of file extensions that the script will process. | `set[str]` | – |
| `DOCS_FOLDER` | Target directory for generated Markdown files. | `Path` (`Path("docs/generated")`) | – |
| `ollama_client` | Instance of `ollama.Client` used to communicate with Ollama. | `Client` | – |
| **Functions** | | | |
| `list_source_files(root_dir: str = ".") -> list[Path]` | Recursively walks `root_dir` and returns a list of source files whose suffix is in `SOURCE_EXTENSIONS`, excluding any path containing `"test"` or `"fixture"` (case‑insensitive). | Input: `root_dir` (default `"."`); Output: `list[Path]` | Public – used by `create_full_documentation`. |
| `generate_doc_for_file(file_path: Path, code: str) -> str` | Constructs a detailed prompt (including the target file path and its source code) and streams the response from Ollama, concatenating all parts into a single Markdown string. | Input: `file_path`, `code`; Output: documentation `str` | Public – core of the documentation generation pipeline. |
| `save_doc(file_path: Path, content: str) -> None` | Ensures the `DOCS_FOLDER` exists, creates a safe filename by replacing path separators with underscores, writes the generated Markdown to that file, and logs the action. | Input: `file_path`, `content`; Output: `None` | Public – persists generated documentation. |
| `create_full_documentation() -> None` | Orchestrates the full workflow: discovers source files, reads each file’s content, generates its documentation, and saves the result. Provides console feedback for progress and errors. | Input: none; Output: `None` | Public – entry point when `app.py` is executed as a script. |
| `if __name__ == "__main__":` | Guard that triggers `create_full_documentation()` when the module is run directly. | – | – |

---

## 3. Dependencies & Relationships

### Imports

| Imported Module | Reason for Import |
|-----------------|-------------------|
| `os` | (Imported but not directly used in current code; could be retained for future extensions.) |
| `json` | (Imported but not directly used; may be useful for future response handling.) |
| `subprocess` | (Imported but not used; possibly intended for external command execution.) |
| `pathlib.Path` | Provides OS‑independent path manipulation and file searching. |
| `dotenv.load_dotenv` | Loads environment variables from a `.env` file (e.g., Ollama connection settings). |
| `ollama.Client` | Communicates with the Ollama inference server to request LLM completions. |

### Interaction with Other Files / Modules

* **Depends on**  
  * The **Ollama server** (via `ollama.Client`) to generate documentation.  
  * The **environment** (via `load_dotenv`) for any required configuration variables (e.g., `OLLAMA_HOST`).  
  * The **source code files** located under the project root that match `SOURCE_EXTENSIONS`.  

* **Potential Dependents**  
  * Any CI/CD pipeline or developer tooling that invokes `python app.py` to refresh documentation.  
  * Scripts that consume the generated Markdown files from `docs/generated` (e.g., static site generators, docs portals).  

* **Architectural Fit**  
  * This module sits at the **automation layer** of the project, bridging the **codebase** with **AI‑assisted documentation**.  
  * It is orthogonal to the main application logic, meaning it can be executed independently without affecting runtime behavior.  

---

## 4. Workflow Description

1. **Environment Preparation**  
   * `load_dotenv()` runs at import time, ensuring any `.env` variables are available for the Ollama client.

2. **File Discovery** (`list_source_files`)  
   * Starting from the current directory (or a supplied root), recursively locate all files whose extensions are in `SOURCE_EXTENSIONS`.  
   * Filter out any paths containing `"test"` or `"fixture"` to avoid documenting test code or fixture data.

3. **Iteration over Files** (`create_full_documentation`)  
   * For each discovered path:  
     a. Attempt to read the file’s content (`Path.read_text`).  
     b. If reading fails, log the error and continue to the next file.

4. **Documentation Generation** (`generate_doc_for_file`)  
   * Build a multi‑line prompt that embeds the file path and raw source code, asking the LLM to produce a structured Markdown document.  
   * Call `ollama_client.chat` with `stream=True` to receive incremental chunks.  
   * Concatenate all chunks into a single string (`response_text`).

5. **Persistence** (`save_doc`)  
   * Ensure the target `docs/generated` directory exists.  
   * Transform the original file path into a safe filename (slashes → underscores) and append `_doc.md`.  
   * Write the Markdown content to disk and print a confirmation message.

6. **Completion**  
   * After processing all files, print a final “Documentation generation complete!” message.

**Call Flow Summary**

```
main (if __name__ == "__main__")
   └─ create_full_documentation()
        ├─ list_source_files()
        └─ for each file:
            ├─ read file → code
            ├─ generate_doc_for_file(file_path, code)
            │    └─ ollama_client.chat(...) (stream)
            └─ save_doc(file_path, doc)
```

---

## 5. Usage Examples

### Running the script manually

```bash
# Ensure Ollama is reachable (e.g., OLLAMA_HOST is set in .env)
python app.py
```

The command will:

* Scan the repository for relevant source files.
* Generate Markdown documentation for each file.
* Store the outputs under `docs/generated/`.

### Invoking programmatically

```python
from pathlib import Path
from app import generate_doc_for_file, save_doc

# Example: generate documentation for a single file
file_path = Path("src/my_module.py")
code = file_path.read_text(encoding="utf-8")

doc_md = generate_doc_for_file(file_path, code)
save_doc(file_path, doc_md)
```

---

## 6. Notes for Developers

* **Streaming vs. Full Response** – The function streams the Ollama response to avoid loading large replies into memory at once. Ensure the Ollama endpoint supports streaming; otherwise, set `stream=False` and adjust handling accordingly.

* **Unused Imports** – `os`, `json`, and `subprocess` are imported but not used. Removing them can clean up the module, or they can be kept if future extensions (e.g., invoking external tools, handling JSON responses) are planned.

* **Error Handling** –  
  * File‑read errors are caught and logged, but LLM‑related errors (network failures, rate limits) are not explicitly handled. Consider wrapping the Ollama call in a `try/except` block to retry or skip problematic files gracefully.  
  * The generated documentation is saved even if the LLM response is empty or malformed; you may want to validate `doc` before persisting.

* **Prompt Size** – For very large source files, the prompt could exceed Ollama’s token limits. Implement chunking or size checks if the project contains giant files.

* **Environment Configuration** – The script relies on environment variables (e.g., `OLLAMA_HOST`). Ensure these are defined in a `.env` file or the shell environment, otherwise the Ollama client may fail to connect.

* **Extensibility** –  
  * Adding more file extensions is as simple as updating `SOURCE_EXTENSIONS`.  
  * Custom filters (e.g., excluding specific directories) can be added to `list_source_files`.  
  * To support non‑streaming models, modify `generate_doc_for_file` to handle a single response object.

* **Concurrency** – Documentation generation is performed sequentially. For large codebases, consider parallelizing the loop (e.g., using `concurrent.futures.ThreadPoolExecutor`) while respecting Ollama’s concurrency limits.

* **Security** – The script sends raw source code to an external LLM service. Verify that the Ollama server runs in a trusted environment, especially for proprietary or sensitive code.

---