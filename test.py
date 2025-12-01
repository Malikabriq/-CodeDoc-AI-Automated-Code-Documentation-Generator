import os
import json
from dotenv import load_dotenv
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from xai_sdk import Client
from typing import Dict, Any, List

load_dotenv()

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
if not GITHUB_REPO or "/" not in GITHUB_REPO:
    raise ValueError("GITHUB_REPOSITORY must be set in environment variables (e.g., 'owner/repo')")

REPO_OWNER, REPO_NAME = GITHUB_REPO.split("/")

pem_path = os.getenv("GITHUB_APP_PRIVATE_KEY")
if pem_path and os.path.exists(pem_path):
    try:
        with open(pem_path, "r") as f:
            os.environ["GITHUB_APP_PRIVATE_KEY"] = f.read()
    except Exception:
        pass

github = GitHubAPIWrapper()
toolkit = GitHubToolkit.from_github_api_wrapper(github)

XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY must be set to use Grok analysis.")
client = Client(api_key=XAI_API_KEY)

tools = {str(i + 1): tool for i, tool in enumerate(toolkit.get_tools())}
GROK_CHOICE = str(len(tools) + 1)

def print_menu():
    print("\n===== GitHub Toolkit CLI =====")
    for key, tool in tools.items():
        print(f"{key}. {tool.name}")
    print(f"{GROK_CHOICE}. Analyze Pull Request with Grok")
    print("0. Exit\n")

def run_tool(choice: str):
    if choice == GROK_CHOICE:
        select_and_analyze_pr()
        return

    tool = tools.get(choice)
    if not tool:
        print("Invalid choice! Try again.")
        return

    try:
        if tool.args_schema:
            fields = list(tool.args_schema.model_fields.keys())
            args: Dict[str, Any] = {}
            for arg_name in fields:
                value = input(f"Enter {arg_name}: ")
                if not value and tool.args_schema.model_fields[arg_name].is_required:
                    print(f"Error: {arg_name} is required.")
                    return
                elif value:
                    try:
                        field_type = tool.args_schema.model_fields[arg_name].annotation
                        args[arg_name] = int(value) if field_type is int else value
                    except ValueError:
                        args[arg_name] = value
            output = tool.run(args)
        else:
            output = tool.run()

        try:
            parsed_output = json.loads(output)
            print(json.dumps(parsed_output, indent=2))
        except (json.JSONDecodeError, TypeError):
            print(output)
    except Exception as e:
        print(f"Error executing {tool.name}: {e}")

def fetch_pr_files(pr_number: str) -> List[Dict[str, str]]:
    if not pr_number or not pr_number.isdigit():
        print("Invalid PR number. Must be a positive integer.")
        return []

    pr_number_int = int(pr_number)
    pr_full_input = {"repo_owner": REPO_OWNER, "repo_name": REPO_NAME, "number": pr_number_int}
    pr_number_input = {"number": pr_number_int}

    try:
        pr_tool = [t for t in toolkit.get_tools() if t.name == "Get Pull Request"][0]
        pr = json.loads(pr_tool.run(pr_full_input))#error 
        files_tool = [t for t in toolkit.get_tools() if t.name == "List Pull Requests' Files"][0]
        pr_files = json.loads(files_tool.run(pr_number_input))
    except Exception as e:
        print("Failed to fetch PR details or file list:", str(e))
        return []

    if not pr_files:
        print("PR found, but it contains no files to analyze.")
        return []

    files_content = []
    read_file_tool = [t for t in toolkit.get_tools() if t.name == "Read File"][0]
    base_branch = pr.get("base", {}).get("ref", os.getenv("GITHUB_BASE_BRANCH", "main"))
    head_branch = pr.get("head", {}).get("ref", os.getenv("GITHUB_BRANCH", "main"))

    for f in pr_files:
        filepath = f.get('filename')
        if not filepath: continue
        try:
            original_content = read_file_tool.run({"file_path": filepath, "branch": base_branch})
        except Exception:
            original_content = ""
        try:
            changed_content = read_file_tool.run({"file_path": filepath, "branch": head_branch})
        except Exception:
            changed_content = ""
        files_content.append({
            "file": filepath,
            "original": original_content,
            "changed": changed_content
        })

    return files_content

def ask_grok_to_analyze(file_diff: Dict[str, str]) -> str:
    prompt = f"""
You are a senior code reviewer. Analyze the changes made to {file_diff['file']}.
Provide a detailed review.

--- ORIGINAL ---
{file_diff['original']}

--- CHANGED ---
{file_diff['changed']}

Provide a markdown report with:
1. Summary of Changes
2. Technical Review (Pros/Cons)
3. Suggestions for Improvement
"""
    try:
        response = client.chat.completions.create(
            model="grok-2-1212",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok API Error: {e}"

def analyze_pr(pr_number: str):
    diffs = fetch_pr_files(pr_number)
    if not diffs:
        print("No files to analyze or PR not found.")
        return
    print(f"\nAnalyzing {len(diffs)} files in PR #{pr_number}...\n")
    for d in diffs:
        review = ask_grok_to_analyze(d)
        print(f"\n=== Grok Review for: {d['file']} ===")
        print(review)
        print("\n-------------------------------------\n")

def select_and_analyze_pr():
    pr_number = input("Enter PR number to analyze: ").strip()
    if not pr_number:
        print("No PR number entered. Aborting.")
        return
    if not pr_number.isdigit():
        print("Invalid PR number. Must be a positive integer.")
        return
    analyze_pr(pr_number)

if __name__ == "_main_":
    # while True:
        print_menu()
        # choice = input("Enter your choice: ").strip()
        # if choice == "0":
        #     print("Exiting...")
        #     break
        # if choice:
        #     run_tool(choice)
        # else:
        #     print("Please enter a valid choice.")