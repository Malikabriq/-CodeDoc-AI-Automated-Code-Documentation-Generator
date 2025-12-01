import importlib.util
import sys
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

# Load app.py as a module
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

fetch_pr_files = app_module.fetch_pr_files

print("Attempting to fetch PR files for PR #2...")

try:
    files = fetch_pr_files("2")
    print(f"Found {len(files)} files.")
    for f in files:
        print(f"File: {f['file']}")
except Exception as e:
    traceback.print_exc()
