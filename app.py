import os
import requests
import subprocess
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("❌ ERROR: GITHUB_TOKEN is not set. Please add it as an environment variable.")

app = FastAPI()

def get_pr_diff(repo, pr_number):
    """Fetch the code changes (diff) from a PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        files = response.json()
        diffs = ""
        for file in files:
            filename = file.get("filename", "Unknown File")
            patch = file.get("patch", "")  # Some files may not have a patch
            diffs += f"\nFile: {filename}\nChanges:\n{patch}\n"

        return diffs if diffs else "No code changes detected."
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching PR diff: {str(e)}"

def analyze_code_with_codellama(code_diff):
    """Send the PR diff to Code Llama (via Ollama) for review."""
    if not code_diff or code_diff == "No code changes detected.":
        return "⚠ No code changes detected. No review needed."

    prompt = f"""
    You are an AI code reviewer specialized in detecting bugs, security issues, and best practices.
    Analyze the following code changes and provide feedback as a numbered list:

    {code_diff}

    Keep feedback concise and actionable.
    """

    try:
        process = subprocess.run(
            ["ollama", "run", "codellama:7b", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if process.returncode != 0:
            return f"❌ Error running Code Llama: {process.stderr}"

        return process.stdout.strip()
    except Exception as e:
        return f"❌ Error analyzing code with Code Llama: {str(e)}"

def post_review_comment(repo, pr_number, feedback):
    """Post AI-generated feedback as a comment on the GitHub PR."""
    if "❌" in feedback or "⚠" in feedback:
        return feedback  # Avoid posting if there was an error

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"### 🤖 AI Code Review Feedback:\n{feedback}"}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"❌ Error posting review comment: {str(e)}"

@app.post("/review")
async def review_pr(request: Request):
    """API endpoint to handle PR review requests."""
    data = await request.json()
    repo = data.get("repo")
    pr_number = data.get("pr")

    if not repo or not pr_number:
        return {"error": "❌ Invalid request. Missing repository or PR number."}

    print(f"🔍 Fetching PR #{pr_number} from {repo}...")

    # Fetch PR code changes
    code_diff = get_pr_diff(repo, pr_number)
    print(code_diff)

    # Analyze with Code Llama via Ollama
    feedback = analyze_code_with_codellama(code_diff)
    print(feedback)

    # Post AI feedback to GitHub PR
    result = post_review_comment(repo, pr_number, feedback)

    return {"message": "AI Review posted on GitHub", "feedback": feedback, "result": result}
