import os
import re
import subprocess
import sys
import tempfile

SPECS_DIR = "specs"
LABEL = "type:spec"

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Don't print error for view failures, just return None
        return None

def parse_spec(file_path):
    """Parse spec file to get title, body, and issue number."""
    with open(file_path, "r") as f:
        content = f.read()

    # Extract Title (First H1)
    title_match = re.search(r"^# Spec: (.+)", content, re.MULTILINE)
    if not title_match:
        title_match = re.search(r"^# (.+)", content, re.MULTILINE)
    
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path)
    if not title.startswith("[Spec]"):
        full_title = f"[Spec] {title}"
    else:
        full_title = title

    # Extract Issue Number
    issue_match = re.search(r"^Issue: #(\d+)", content, re.MULTILINE)
    issue_number = issue_match.group(1) if issue_match else None

    # The body we send to GitHub (keeping it simple: use the whole file content)
    body = content
    
    return {
        "title": full_title,
        "body": body,
        "issue_number": issue_number
    }

def update_file_with_issue(file_path, issue_number):
    """Insert 'Issue: #123' after the first line (Title)."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    insert_idx = 1
    if lines and lines[0].startswith("#"):
        insert_idx = 1
    
    for line in lines[:5]:
        if line.strip().startswith("Issue: #"):
            return 
            
    lines.insert(insert_idx, f"Issue: #{issue_number}\n")
    
    with open(file_path, "w") as f:
        f.writelines(lines)
    print(f"Updated {file_path} with Issue #{issue_number}")

def get_remote_body(issue_number):
    """Fetch current body from GitHub."""
    import json
    cmd = f"gh issue view {issue_number} --json body"
    output = run_command(cmd)
    if output:
        try:
            data = json.loads(output)
            return data.get("body", "").strip()
        except:
            return None
    return None

def main():
    if not os.path.exists(SPECS_DIR):
        print(f"Directory {SPECS_DIR} not found.")
        return

    for filename in sorted(os.listdir(SPECS_DIR)):
        if not filename.endswith(".md") or filename == "README.md":
            continue
        
        file_path = os.path.join(SPECS_DIR, filename)
        spec_data = parse_spec(file_path)
        
        if spec_data["issue_number"]:
            print(f"Checking {filename} (Issue #{spec_data['issue_number']})...")
            remote_body = get_remote_body(spec_data["issue_number"])
            
            # Compare (stripping whitespace to be robust)
            if remote_body and remote_body.strip() == spec_data["body"].strip():
                print(f"  -> Up to date.")
            else:
                print(f"  -> Content changed. Updating GitHub...")
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tf:
                    tf.write(spec_data["body"])
                    temp_name = tf.name
                
                cmd = f"gh issue edit {spec_data['issue_number']} --title '{spec_data['title']}' --body-file '{temp_name}'"
                run_command(cmd)
                os.remove(temp_name)
                print(f"  -> Successfully updated Issue #{spec_data['issue_number']}")
        else:
            print(f"Creating Issue for {filename}...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tf:
                tf.write(spec_data["body"])
                temp_name = tf.name
            
            cmd = f"gh issue create --title '{spec_data['title']}' --body-file '{temp_name}' --label '{LABEL}'"
            output = run_command(cmd)
            os.remove(temp_name)
            
            if output:
                match = re.search(r"/issues/(\d+)", output)
                if match:
                    new_issue_num = match.group(1)
                    print(f"  -> Created Issue #{new_issue_num}")
                    update_file_with_issue(file_path, new_issue_num)

if __name__ == "__main__":
    main()