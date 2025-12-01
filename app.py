import os
import json
import subprocess
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


def generate_doc_for_file(file_path: Path, code: str) -> str:
    prompt = f"""
You are a senior software architect and technical writer.

Your task is to generate high-quality, professional documentation for the following source file.

File Path: {file_path}

Source Code:
{code}

Generate detailed developer documentation in Markdown including:

## 1. Module Purpose
- What this file is responsible for.
- Why it exists in the project.

## 2. Key Components
For each class, function, or significant block:
- What it does
- Inputs and outputs (with types if inferable)
- Internal logic overview
- Any public API exposed

## 3. Dependencies & Relationships
- List all imports
- Explain how this file interacts with other files/modules in the project
- Mention:
  - Which components this file depends on
  - Which components depend on this file (infer logically)
  - How it fits into the overall architecture

## 4. Workflow Description
- Step-by-step explanation of how the file works internally
- Call flow summary

## 5. Usage Examples
- Code usage examples ONLY if clearly inferable from functions/classes

## 6. Notes for Developers
- Pitfalls, limitations, assumptions, or important patterns used

Output strictly in clean, well-formatted Markdown. Do not add fictional code. Use only what is present or logically inferable.
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
    print(f"Found {len(files)} source files to document.\n")

    for file_path in files:
        print(f"Generating docs for: {file_path}")
        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  Could not read {file_path}: {e}")
            continue

        doc = generate_doc_for_file(file_path, code)
        save_doc(file_path, doc)

    print("📘 Documentation generation complete!")


if __name__ == "__main__":
    create_full_documentation()
