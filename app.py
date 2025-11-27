import os
import json
from dotenv import load_dotenv
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from xai_sdk import Client

load_dotenv()

pem_path = os.getenv("GITHUB_APP_PRIVATE_KEY")
with open(pem_path, "r") as f:
    os.environ["GITHUB_APP_PRIVATE_KEY"] = f.read()

github = GitHubAPIWrapper()
toolkit = GitHubToolkit.from_github_api_wrapper(github)

client = Client(api_key=os.getenv("XAI_API_KEY"))

tools = {str(i+1): tool for i, tool in enumerate(toolkit.get_tools())}

def print_menu():
    for key, tool in tools.items():
        print(f"{key}. {tool.name}")
    print(f"{len(tools)+1}. Analyze Pull Request with Grok")
    print("0. Exit\n")

def run_tool(choice):
    if choice == str(len(tools)+1):
        analyze_pr()
        return

    # Normal GitHub tool
    tool = tools.get(choice)
    if not tool:
        print("Invalid choice! Try again.")
        return

    if tool.args_schema:
        fields = list(tool.args_schema.model_fields.keys())
        if len(fields) == 1:
            value = input(f"Enter {fields[0]}: ")
            output = tool.run(value)
        else:
            args = {}
            for arg_name in fields:
                value = input(f"Enter {arg_name}: ")
                args[arg_name] = value
            output = tool.run(**args)
    else:
        output = tool.run()

    print("\n--- Output ---")
    print(output)
    print("--------------\n")

# --- PR Analyzer ---
def analyze_pr():
    try:
        pr_number = input("Enter PR number to analyze: ").strip()
        if not pr_number.isdigit():
            print("Invalid PR number.")
            return
        pr_number = int(pr_number)

        # Get tools
        get_pr_tool = [t for t in toolkit.get_tools() if t.name == "Get Pull Request"][0]
        list_files_tool = [t for t in toolkit.get_tools() if t.name == "List Pull Requests' Files"][0]
        read_file_tool = [t for t in toolkit.get_tools() if t.name == "Read File"][0]

        # Fetch PR details
        pr_details_raw = get_pr_tool.run({"pr_number": pr_number})
         # Convert JSON string to dict if needed
        pr_details = json.loads(pr_details_raw) if isinstance(pr_details_raw, str) else pr_details_raw

        # Fetch files changed in PR
        pr_files_raw = list_files_tool.run({"pr_number": pr_number})
        pr_files = json.loads(pr_files_raw) if isinstance(pr_files_raw, str) else pr_files_raw
        if not pr_files:
            print("No files found in this PR.")
            return

        print("\n===== Grok PR Analysis =====\n")
        for f in pr_files:
            filename = f['filename']

            # Read original and changed files
            original = read_file_tool.run({"file_path": filename, "branch": pr_details['base']['ref']})
            changed = read_file_tool.run({"file_path": filename, "branch": pr_details['head']['ref']})

            # Grok prompt
            prompt = f"""
You are a senior code reviewer.
Compare original and changed versions of the file `{filename}`.

--- ORIGINAL ---
{original}

--- CHANGED ---
{changed}

Provide a detailed review:
- What changed
- Pros/cons
- Suggestions
"""
            response = client.chat.completions.create(
                model="grok-2-1212",
                messages=[{"role": "user", "content": prompt}]
            )

            print(f"\n=== Review for {filename} ===\n")
            print(response.choices[0].message.content)
            print("\n---------------------------\n")

    except Exception as e:
        print(f"Failed to analyze PR: {e}")

if __name__ == "__main__":
    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("Exiting... Goodbye!")
            break
        run_tool(choice)
