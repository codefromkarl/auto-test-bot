import subprocess
import sys
import os
import datetime
import json

# Configuration
BUG_LABEL = "bug"
REPO_OWNER = "codefromkarl" # Assuming based on previous context
REPO_NAME = "auto-test-bot"

def run_spec(spec_id):
    print(f"🚀 Starting Test Execution for {spec_id}...")
    
    # Mapping Spec ID to Workflow File
    # Based on Spec definitions
    SPEC_TO_WORKFLOW = {
        "NH-SMOKE-001": "workflows/at/naohai_05_create_story_to_video_e2e.yaml",
        "NH-E2E-001": "workflows/e2e/naohai_E2E_GoldenPath.yaml",
        "NH-CREATE-001": "workflows/fc/naohai_FC_NH_012_rf.yaml", # Defaulting to full creation
        "NH-SCRIPT-001": "workflows/fc/naohai_FC_NH_034_rf.yaml", # Analysis & Script
        "NH-IMAGE-001": "workflows/fc/naohai_FC_NH_040_rf.yaml",  # Image Gen
        "NH-VIDEO-001": "workflows/fc/naohai_FC_NH_042_rf.yaml",  # Video Creation
        "NH-EXPORT-001": "workflows/fc/naohai_FC_NH_050_rf.yaml", # Export
    }
    
    workflow_file = SPEC_TO_WORKFLOW.get(spec_id)
    if not workflow_file:
        print(f"❌ Unknown Spec ID: {spec_id}. Please check mapping in tools/run_and_report.py")
        return False, "", "Unknown Spec ID"

    if not os.path.exists(workflow_file):
        print(f"❌ Workflow file not found: {workflow_file}")
        return False, "", f"File not found: {workflow_file}"

    # Construct command
    cmd = f"python3 src/main_workflow.py --workflow {workflow_file}"
    
    print(f"📝 Mapped {spec_id} -> {workflow_file}")
    print(f"📝 Command: {cmd}")
    
    start_time = datetime.datetime.now()
    
    try:
        # Run command and capture output
        process = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1200 # 20 mins timeout
        )
        
        duration = datetime.datetime.now() - start_time
        
        print(f"⏱️ Duration: {duration}")
        
        if process.returncode == 0:
            print("✅ Test PASSED")
            print("-" * 20)
            print(process.stdout[-500:]) # Show last 500 chars
            return True, process.stdout, process.stderr
        else:
            print("❌ Test FAILED")
            return False, process.stdout, process.stderr
            
    except subprocess.TimeoutExpired:
        print("❌ Test TIMEOUT")
        return False, "Timeout", "Timeout"
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return False, "", str(e)

def create_bug_report(spec_id, stdout, stderr):
    print("\n🚨 Preparing Bug Report...")
    
    # 1. Symptom (Extract last few lines of stderr or stdout)
    symptom = "Test execution failed."
    if stderr:
        lines = stderr.strip().split('\n')
        symptom = "\n".join(lines[-10:])
    elif stdout:
        lines = stdout.strip().split('\n')
        # Look for "Error" or "Fail"
        error_lines = [l for l in lines if "Error" in l or "Fail" in l]
        if error_lines:
            symptom = "\n".join(error_lines[-5:])
        else:
            symptom = "\n".join(lines[-10:])

    # 2. Repro Command
    repro = f"python3 src/main_workflow.py --spec {spec_id}"
    
    # 3. Expected vs Actual
    expected_actual = f"Expected: {spec_id} execution should pass with exit code 0.\nActual: Execution failed with exit code 1."

    # 4. Logs (Wrap in code block)
    # Using explicit string concatenation to avoid triple-quote nesting issues
    stdout_snip = stdout[-2000:] if stdout else "(No stdout)"
    stderr_snip = stderr[-2000:] if stderr else "(No stderr)"
    
    logs = f"""
<details>
<summary>Stdout</summary>

```
{stdout_snip}
```
</details>

<details>
<summary>Stderr</summary>

```
{stderr_snip}
```
</details>
"""

    # Construct Body for gh issue create
    body_markdown = f"""
### ❗ Symptom（现象）
```
{symptom}
```

### 🔁 Repro Command（复现命令）
```bash
{repro}
```

### ⚖️ Expected vs Actual
{expected_actual}

### 📄 Logs / Evidence
{logs}

### 🤖 Auto-Reported
This bug was automatically detected and reported by the Test Agent.
"""

    # Save to temp file
    with open("temp_bug_body.md", "w") as f:
        f.write(body_markdown)
        
    print("📝 Bug report draft saved to 'temp_bug_body.md'.")
    print("🚀 Submitting to GitHub...")
    
    title = f"[Bug] {spec_id} Execution Failed"
    
    try:
        cmd = ["gh", "issue", "create", "--title", title, "--body-file", "temp_bug_body.md", "--label", BUG_LABEL]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
        print(f"✅ Bug Issue Created: {result.stdout.strip()}")
        os.remove("temp_bug_body.md")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/run_and_report.py <SPEC_ID>")
        sys.exit(1)
        
    spec_id = sys.argv[1]
    success, out, err = run_spec(spec_id)
    
    if not success:
        create_bug_report(spec_id, out, err)
        sys.exit(1)
    
    sys.exit(0)
