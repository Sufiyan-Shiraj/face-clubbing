import urllib.request
import json
import time

url = "https://api.github.com/repos/Sufiyan-Shiraj/face-clubbing/actions/runs"
req = urllib.request.Request(url, headers={"User-Agent": "CatLog-CI-Checker"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        runs = data.get("workflow_runs", [])
        if not runs:
            print("No workflow runs found.")
        for r in runs[:5]:
            print(f"ID: {r['id']} | Name: {r['name']} | Event: {r['event']} | Branch/Tag: {r.get('head_branch')} | Status: {r['status']} | Conclusion: {r['conclusion']} | URL: {r['html_url']}")
            
            # Check individual jobs for the latest release run
            if r['name'] == "Release CatLog":
                jobs_url = r['jobs_url']
                jobs_req = urllib.request.Request(jobs_url, headers={"User-Agent": "CatLog-CI-Checker"})
                try:
                    with urllib.request.urlopen(jobs_req, timeout=10) as jresp:
                        jdata = json.loads(jresp.read().decode("utf-8"))
                        for j in jdata.get("jobs", []):
                            print(f"   -> Job: {j['name']} | Status: {j['status']} | Conclusion: {j['conclusion']}")
                except Exception as je:
                    print(f"   Could not fetch jobs: {je}")
except Exception as e:
    print(f"Error checking GitHub Actions API: {e}")
