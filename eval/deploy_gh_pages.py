import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

bundle_dir = REPO_ROOT / "eval" / "synthetic_bundle"
index_file = REPO_ROOT / ".git" / "temp_gh_pages_index"

if index_file.exists():
    index_file.unlink()

env = dict(os.environ)
env["GIT_INDEX_FILE"] = str(index_file)
env["GIT_WORK_TREE"] = str(bundle_dir)

# 1. Add all files in synthetic bundle to temporary git index
res = subprocess.run(["git", "add", "-A", "."], cwd=bundle_dir, env=env, capture_output=True, text=True)
print(f"git add exit code: {res.returncode}")
if res.stderr:
    print(res.stderr)

# 2. Write tree
res = subprocess.run(["git", "write-tree"], cwd=bundle_dir, env=env, capture_output=True, text=True)
tree_sha = res.stdout.strip()
print(f"tree SHA: {tree_sha}")

# 3. Create orphan commit
commit_msg = "deploy: publish 20-photo privacy-safe synthetic bundle to GitHub Pages"
res = subprocess.run(["git", "commit-tree", tree_sha, "-m", commit_msg], cwd=bundle_dir, env=env, capture_output=True, text=True)
commit_sha = res.stdout.strip()
print(f"commit SHA: {commit_sha}")

# 4. Push commit to origin gh-pages
res = subprocess.run(["git", "push", "origin", f"{commit_sha}:refs/heads/gh-pages", "--force"], cwd=REPO_ROOT, capture_output=True, text=True)
print(f"git push exit code: {res.returncode}")
print(f"git push stdout: {res.stdout}")
print(f"git push stderr: {res.stderr}")

# 5. Clean up temporary index
if index_file.exists():
    index_file.unlink()

if res.returncode == 0:
    print("\nSUCCESSFULLY PUSHED TO gh-pages!")
    print("URL: https://sufiyan-shiraj.github.io/face-clubbing/")
else:
    print("\nFAILED TO PUSH TO gh-pages")
