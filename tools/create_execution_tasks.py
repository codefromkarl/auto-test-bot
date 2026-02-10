import os
import re
import subprocess
import time

SPECS_DIR = "specs"

def run_command(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}\n{e.stderr}")
        return None

def get_specs():
    specs = []
    if not os.path.exists(SPECS_DIR):
        return specs
        
    for filename in sorted(os.listdir(SPECS_DIR)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
            
        with open(os.path.join(SPECS_DIR, filename), "r") as f:
            content = f.read()
            
        # Extract ID (filename base)
        spec_id = filename.replace(".md", "")
        
        # Extract Title
        title_match = re.search(r"^# Spec: (.+)", content, re.MULTILINE)
        if not title_match:
             title_match = re.search(r"^# (.+)", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else spec_id
        
        # Extract Spec Issue Number
        issue_match = re.search(r"^Issue: #(\d+)", content, re.MULTILINE)
        spec_issue = issue_match.group(1) if issue_match else None
        
        specs.append({
            "id": spec_id,
            "title": title,
            "spec_issue": spec_issue
        })
    return specs

def create_task(spec):
    print(f"Creating task for {spec['id']}...")
    
    task_title = f"[Task] Execute {spec['id']}: {spec['title']}"
    
    spec_ref = f"#{spec['spec_issue']}" if spec['spec_issue'] else spec['id']
    
    body = f"""### 🎯 Goal
Execute the tests defined in Spec {spec_ref} to verify current system status.

### 📥 Inputs
- **Spec**: {spec_ref}
- **Playbook**: `AI_EXECUTION_PLAYBOOK.md`

### 📤 Outputs
- **Local Evidence**: `runs/YYYY-MM-DD/{spec['id']}-run.md`
- **Report**: HTML Report & Logs
- **Bugs**: New issues for any deviations found (type:bug)

### ✅ DoD
- [ ] Test execution completed (Pass or Fail)
- [ ] Run evidence file created in `runs/` directory
- [ ] Results updated in the Task comments or closed with summary
"""

    # Using temp file for body to avoid shell escaping hell
    with open("temp_task_body.md", "w") as f:
        f.write(body)
        
    cmd = f"gh issue create --title '{task_title}' --body-file 'temp_task_body.md' --label 'type:task,ai:auto-fix,status:ready'"
    output = run_command(cmd)
    
    if os.path.exists("temp_task_body.md"):
        os.remove("temp_task_body.md")
        
    if output:
        print(f"✅ Created Task: {output}")
    else:
        print(f"❌ Failed to create task for {spec['id']}")
    
    # Sleep to avoid rate limits
    time.sleep(1)

if __name__ == "__main__":
    specs = get_specs()
    print(f"Found {len(specs)} specs. Creating execution tasks...")
    for spec in specs:
        create_task(spec)
