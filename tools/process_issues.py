import json
import os
import sys

def main():
    ai_dir = ".ai"
    issues_dir = os.path.join(ai_dir, "issues")
    raw_json_path = os.path.join(ai_dir, "issues_graphql.json")
    index_path = os.path.join(ai_dir, "index.md")
    active_path = os.path.join(ai_dir, "ACTIVE.md")

    status_filter = os.environ.get("STATUS_FILTER", "")

    try:
        with open(raw_json_path, "r") as f:
            data = json.load(f)
            # Handle GraphQL response structure
            if "errors" in data:
                print(f"GraphQL Errors: {data.get('errors')}")
                sys.exit(1)
            issues = data.get("data", {}).get("repository", {}).get("issues", {}).get("nodes", [])
    except Exception as e:
        print(f"Error loading JSON: {e}")
        sys.exit(1)

    # Clear old issues
    if os.path.exists(issues_dir):
        for f in os.listdir(issues_dir):
            os.remove(os.path.join(issues_dir, f))
    else:
        os.makedirs(issues_dir)

    index_content = "# Current Issues Index\n"
    if status_filter:
        index_content += f"> Filtered by Project Status: **{status_filter}**\n\n"
    else:
        index_content += f"> Showing ALL Open Issues\n\n"

    # Use explicit newline characters instead of multiline string for safety
    index_content += "| ID | Title | Status | Project Status | Assignee |\n"
    index_content += "|---|---|---|---|---|\n"

    synced_count = 0

    for issue in issues:
        number = issue.get("number")
        title = issue.get("title", "").replace("|", r"\|")
        body = issue.get("body", "") or "(No description)"
        state = issue.get("state", "")
        url = issue.get("url", "")
        
        # Process Assignees
        assignees = ", ".join([a["login"] for a in issue.get("assignees", {}).get("nodes", [])])
        
        # Process Labels
        label_nodes = issue.get("labels", {}).get("nodes", [])
        labels_list = [l["name"] for l in label_nodes]
        labels = ", ".join(labels_list)

        # AI LABEL FILTER
        # Only sync issues that have at least one label starting with "ai:"
        has_ai_label = any(l.lower().startswith("ai:") for l in labels_list)
        if not has_ai_label:
            continue
        
        # Process Project Status
        project_status = "No Status"
        project_items = issue.get("projectItems", {}).get("nodes", [])
        if project_items:
            # Assuming we take the status from the first project found
            val = project_items[0].get("fieldValueByName")
            if val:
                project_status = val.get("name", "No Status")
        
        # FILTER LOGIC
        if status_filter and status_filter.lower() != project_status.lower():
            continue

        synced_count += 1
        
        filename = f"ISSUE-{number}.md"
        filepath = os.path.join(issues_dir, filename)
        
        # Add to index
        index_content += f"| [{number}](issues/{filename}) | {title} | {state} | {project_status} | {assignees} |\n"
        
        # Create issue file
        with open(filepath, "w") as f:
            f.write(f"# Issue #{number}: {title}\n\n")
            f.write(f"- **Status**: {state}\n")
            f.write(f"- **Project Status**: {project_status}\n")
            f.write(f"- **Assignee**: {assignees}\n")
            f.write(f"- **Labels**: {labels}\n")
            f.write(f"- **URL**: {url}\n\n")
            f.write("## Description\n\n")
            f.write(body + "\n\n")
            
            comments = issue.get("comments", {}).get("nodes", [])
            if comments:
                f.write("## Comments\n\n")
                for comment in comments:
                    author = comment.get("author", {}).get("login", "Unknown")
                    c_body = comment.get("body", "")
                    f.write(f"### {author}\n\n{c_body}\n\n---\n\n")

    # Write Index
    with open(index_path, "w") as f:
        f.write(index_content)

    # Write ACTIVE.md
    active_content = "# AI Active Context\n\n## 🎯 Instructions for AI\n\n1.  **Read the Index**: Start by reading `.ai/index.md` to see available tasks.\n2.  **Select Task**: Choose the issue assigned to you or marked with the requested status.\n3.  **Read Details**: Read the specific `.ai/issues/ISSUE-XXX.md` file for full context, requirements, and history.\n4.  **Execute**: Perform the task.\n5.  **Record Evidence**: Save all run logs and evidence to `runs/YYYY-MM-DD/`.\n6.  **Update**: If you find new info, update the local file or ask the user to comment on the real issue.\n\n## 📂 Quick Links\n- [Issue Index](index.md)\n"

    with open(active_path, "w") as f:
        f.write(active_content)

    print(f"Synced {synced_count} issues to {issues_dir}")
    print(f"Generated {index_path} and {active_path}")

if __name__ == "__main__":
    main()
