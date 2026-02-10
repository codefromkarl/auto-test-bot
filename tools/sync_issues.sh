#!/bin/bash
# Sync GitHub Issues (with Project Status) to local .ai/ directory
# Usage: 
#   ./tools/sync_issues.sh --status "Ready"
#   ./tools/sync_issues.sh --status "In Progress"
#   ./tools/sync_issues.sh (syncs ALL open issues)

set -e

AI_DIR=".ai"
ISSUES_DIR="$AI_DIR/issues"
RAW_JSON="$AI_DIR/issues_graphql.json"
REPO_INFO_JSON="$AI_DIR/repo_info.json"

# Parse arguments
STATUS_FILTER=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --status) STATUS_FILTER="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Create directories
mkdir -p "$ISSUES_DIR"

# Get Repo Info
gh repo view --json owner,name > "$REPO_INFO_JSON"
OWNER=$(jq -r .owner.login "$REPO_INFO_JSON")
REPO=$(jq -r .name "$REPO_INFO_JSON")

echo "Fetching issues from $OWNER/$REPO via GraphQL..."

# GraphQL Query to fetch issues with Project Status
# Note: Fetches top 50 open issues. Paging not implemented for simplicity yet.
gh api graphql -F owner="$OWNER" -F repo="$REPO" -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    issues(first: 50, states: OPEN) {
      nodes {
        number
        title
        body
        url
        state
        assignees(first: 5) { nodes { login } }
        labels(first: 10) { nodes { name } }
        comments(last: 20) { nodes { author { login } body } }
        projectItems(first: 5) {
          nodes {
            project { title }
            fieldValueByName(name: "Status") {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
          }
        }
      }
    }
  }
}' > "$RAW_JSON"

# Python script to process and filter
export STATUS_FILTER
python3 tools/process_issues.py

# Clean up temporary files
rm "$REPO_INFO_JSON" "$RAW_JSON"
