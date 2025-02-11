import os
import requests
import subprocess
from fastapi import FastAPI, Request

# Load GitHub Token from environment variables
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
        response.raise_for_status()  # Raise an error for bad status codes

        files = response.json()
        diffs = ""
        for file in files:
            filename = file.get("filename", "Unknown File")
            patch = file.get("patch", "")  # Some files may not have a patch
            diffs += f"\nFile: {filename}\nChanges:\n{patch}\n"

        if not diffs:
            return "No code changes detected."

        return diffs
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching PR diff: {str(e)}"

def analyze_code_with_mistral(code_diff):
    """Send the PR diff to Mistral (via Ollama) for review."""
    if not code_diff or code_diff == "No code changes detected.":
        return "⚠ No code changes detected. No review needed."

    prompt = f"""
    You are an AI code reviewer. Review the following code changes for best practices, potential bugs, and optimizations.

    {code_diff}

    Provide detailed feedback as a numbered list.
    """

    try:
        process = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True,
            timeout=60  # Ensure it doesn't hang indefinitely
        )

        if process.returncode != 0:
            return f"❌ Error running Mistral: {process.stderr}"

        return process.stdout.strip()
    except Exception as e:
        return f"❌ Error analyzing code with Mistral: {str(e)}"

def post_review_comment(repo, pr_number, feedback):
    """Post AI-generated feedback as a comment on the GitHub PR."""
    if "❌" in feedback or "⚠" in feedback:
        return feedback  # Don't post comments if there was an error

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

    # Analyze with Mistral via Ollama
    feedback = analyze_code_with_mistral(code_diff)

    # Post AI feedback to GitHub PR
    result = post_review_comment(repo, pr_number, feedback)

    return {"message": "AI Review posted on GitHub", "feedback": feedback, "result": result}
