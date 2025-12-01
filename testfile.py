import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_MODEL = "gpt-oss:120b-cloud"
SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go"}
DOCS_FOLDER = Path("docs/generated")

ollama_client = Client()


def list_source_files(root_dir="."):
    files = []
    for path in Path(root_dir).rglob("*"):
        if (
            path.suffix in SOURCE_EXTENSIONS
            and "test" not in str(path).lower()
            and "fixture" not in str(path).lower()
        ):
            files.append(path)
    return files


def build_dependency_map(files):
    """Very simple static dependency detector.
       Reads import lines and notes relationships between files."""
    dependency_map = {str(f): [] for f in files}

    for file_path in files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for other in files:
            if other == file_path:
                continue

            name = other.stem
            if f"import {name}" in content or f"from {name}" in content:
                dependency_map[str(file_path)].append(str(other))

    return dependency_map


def generate_doc_for_file(file_path: Path, code: str, related_files: list[str]) -> str:
    related_text = "\n".join(f"- {p}" for p in related_files) if related_files else "None detected"

    prompt = f"""
You are a senior software architect and technical writer.
Generate  professional  documentation.

# File
{file_path}

# Related Modules
List of source files that this file imports or depends on:
{related_text}

# Source Code
{code}

# Documentation Requirements (IMPORTANT)
Write extremely high-quality documentation using the following sections:

## Overview
A concise overview of what this module does and why it exists.

## Key Concepts
Summaries of important ideas, algorithms, or patterns used in this module.

## Main Classes & Functions
Describe each important class or function:
- Purpose
- Parameters
- Return values
- Behavior details
- Side effects

## Module Relationships
Explain how this file interacts with the modules listed above.
Describe:
- What it imports
- How it uses those modules
- Whether it acts as a core component, helper, utility, etc.

## Usage Examples
Provide example usage based on best-guess behavior from the code.

## Notes for Developers
Add professional insights:
- design choices
- extension points
- risks
- performance notes

# Output Format
Your entire output MUST be clean Markdown, highly structured, and professional.
"""

    response_text = ""
    stream = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for part in stream:
        response_text += part["message"]["content"]

    return response_text


def save_doc(file_path: Path, content: str):
    DOCS_FOLDER.mkdir(parents=True, exist_ok=True)
    safe_name = str(file_path).replace("/", "_").replace("\\", "_") + "_doc.md"
    path = DOCS_FOLDER / safe_name

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📝 Saved documentation: {path}")


def create_full_documentation():
    files = list_source_files()
    dependency_map = build_dependency_map(files)

    print(f"Found {len(files)} source files to document.\n")

    for file_path in files:
        print(f"Generating docs for: {file_path}")

        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  Could not read {file_path}: {e}")
            continue

        related = dependency_map[str(file_path)]

        doc = generate_doc_for_file(file_path, code, related)
        save_doc(file_path, doc)

    print("📘 Documentation generation complete!")


if __name__ == "__main__":
    create_full_documentation()
