import os
import requests
import subprocess
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# Load GitHub Token from environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI()

def get_pr_diff(repo, pr_number):
    """Fetch the code changes (diff) from a PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    response = requests.get(url, headers=headers).json()
    
    diffs = ""
    for file in response:
        filename = file["filename"]
        patch = file.get("patch", "")
        diffs += f"\nFile: {filename}\nChanges:\n{patch}\n"

    return diffs

def analyze_code_with_mistral(code_diff):
    """Send the PR diff to Mistral (via Ollama) for review."""
    prompt = f"""
    You are an AI code reviewer. Review the following code changes for best practices, potential bugs, and optimizations.

    {code_diff}

    Provide detailed feedback as a numbered list.
    """

    process = subprocess.run(
        ["ollama", "run", "mistral", prompt],
        capture_output=True,
        text=True
    )

    return process.stdout.strip()

def post_review_comment(repo, pr_number, feedback):
    """Post AI-generated feedback as a comment on the GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"### 🤖 AI Code Review Feedback:\n{feedback}"}

    response = requests.post(url, json=data, headers=headers)
    return response.json()

@app.post("/review")
async def review_pr(request: Request):
    """API endpoint to handle PR review requests."""
    data = await request.json()
    repo = data["repo"]
    pr_number = data["pr"]

    # Fetch PR code changes
    code_diff = get_pr_diff(repo, pr_number)

    # Analyze with Mistral via Ollama
    feedback = analyze_code_with_mistral(code_diff)

    # Post AI feedback to GitHub PR
    post_review_comment(repo, pr_number, feedback)

    return {"message": "AI Review posted on GitHub"}
