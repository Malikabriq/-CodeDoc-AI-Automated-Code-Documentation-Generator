# CodeDoc AI 🚀

**Automated Code Documentation Generator for Developers**

---

## Overview

**CodeDoc AI** is an intelligent tool that automatically reads your codebase, analyzes each file, and generates professional, structured, developer-friendly documentation in Markdown format. It provides detailed insights into modules, functions, classes, dependencies, workflows, and cross-file relationships — saving hours of manual effort.

Designed for developers and teams, CodeDoc AI ensures that your documentation is always accurate, consistent, and ready for production use.

---

## Key Features

### 📄 Automated File Documentation
- Supports multiple languages: **Python, JavaScript, TypeScript, Java, Go**.
- Generates Markdown documentation for every source file.
- Explains module purpose, key classes/functions, input/output types, and workflows.

### 🔗 Cross-File Relationship Mapping
- Detects dependencies and imports between files.
- Describes how each file fits into the overall architecture.
- Provides insights into components that depend on or are depended on by this file.

### 🛠 AI-Powered Analysis
- Powered by advanced language models (**Ollama GPT-OSS 120B Cloud**).
- Produces professional, official-style documentation.
- Avoids hallucinations; documentation is strictly based on actual code.

### 📦 Organized Output
- Saves generated documentation in `docs/generated/`.
- Each file receives a separate, clean Markdown document.

### ⚡ Easy to Use
- One command generates docs for the entire repository.
- Fully automated pipeline, no manual intervention required.

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/Malikabriq/-CodeDoc-AI-Automated-Code-Documentation-Generator.git
cd -CodeDoc-AI-Automated-Code-Documentation-Generator
Create a virtual environment

bash
Copy code
python -m venv venv
Activate the environment

On Windows:

powershell
Copy code
venv\Scripts\activate
On Linux/macOS:

bash
Copy code
source venv/bin/activate
Install dependencies

bash
Copy code
pip install -r requirements.txt
Usage
Ensure your .env file is properly configured with your Ollama API key.

Run the documentation generator:

bash
Copy code
python main.py
Generated documentation will be saved in docs/generated/.

Example Output
markdown
Copy code
# File: app/db.py

## Module Purpose
This module handles database connections and session management.

## Key Classes and Functions
- `get_session()`: Provides a SQLAlchemy session object.
- `init_db()`: Initializes database tables.

## Dependencies
- SQLAlchemy
- app/models.py

## Relationships
- Used by `app/crud.py` and `app/main.py`

## Usage
```python
from app.db import get_session

with get_session() as session:
    # your DB operations
yaml
Copy code

---

## Contributing

Contributions are welcome! Please follow standard GitHub workflow:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to your branch (`git push origin feature-name`)
5. Open a Pull Request

---

## License

MIT License © 2025 [Muhammad Abriq](https://github.com/Malikabriq)

---

## Contact

- GitHub: [https://github.com/Malikabriq](https://github.com/Malikabriq)
- Email: your-email@example.com

---

**CodeDoc AI** — Save time, maintain quality, and keep your codebase well-documented effortlessly.
