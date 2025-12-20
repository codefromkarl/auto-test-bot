#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from typing import List, Dict, Any, Optional


AI_LABELS = {"ai:auto-fix", "ai:analysis-only", "ai:manual-only"}
AGENT_PREFIX = "agent:"
COMPONENT_PREFIX = "component:"


def run(cmd: List[str]) -> str:
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def extract_field(field_header: str, text: str) -> str:
    pattern = re.compile(rf"###\s+{re.escape(field_header)}[\s\S]*?\n\n([^\n]+)", re.I)
    match = pattern.search(text)
    return match.group(1).strip().lower() if match else ""


def normalize_component(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    normalized = re.sub(r"^-+|-+$", "", normalized)
    return normalized[:32]


def route_by_component(component: str) -> Optional[str]:
    if not component:
        return None
    if "ci" in component or "github actions" in component:
        return "agent:codex"
    if "runner" in component or "workflow" in component:
        return "agent:codex"
    if "parallel" in component:
        return "agent:codex"
    if "robot" in component:
        return "agent:claude"
    if "auth" in component or "token" in component:
        return "agent:gemini"
    if "service" in component or "endpoint" in component or "9020" in component:
        return "agent:gemini"
    if "data" in component or "fixtures" in component:
        return "agent:gemini"
    if "spec" in component:
        return "agent:claude"
    return None


def fallback_agent(text: str) -> Optional[str]:
    if "github actions" in text or ".yml" in text or "workflow" in text:
        return "agent:codex"
    if "robot" in text or "suite" in text or "tag" in text:
        return "agent:claude"
    if "token" in text or "auth" in text or "9020" in text:
        return "agent:gemini"
    if "parallel" in text or "executor" in text:
        return "agent:codex"
    return None


def build_labels(issue: Dict[str, Any]) -> List[str]:
    labels = {label["name"] for label in issue.get("labels", [])}
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    text = f"{title}\n{body}".lower()

    to_add: List[str] = []

    component = extract_field("🧩 component（组件/归类）", body)
    ai_action = extract_field("🤖 ai action（自动处理策略）", body)

    if not labels.intersection(AI_LABELS):
        if "auto-fix" in ai_action:
            to_add.append("ai:auto-fix")
        elif "manual-only" in ai_action:
            to_add.append("ai:manual-only")
        else:
            to_add.append("ai:analysis-only")

    if not any(label.startswith(AGENT_PREFIX) for label in labels):
        agent = route_by_component(component)
        if not agent:
            agent = fallback_agent(text)
        if agent:
            to_add.append(agent)

    if not any(label.startswith(COMPONENT_PREFIX) for label in labels):
        if component:
            to_add.append(f"{COMPONENT_PREFIX}{normalize_component(component)}")

    return to_add


def main() -> int:
    issues_json = run([
        "gh",
        "issue",
        "list",
        "--state",
        "open",
        "--limit",
        "200",
        "--json",
        "number,title,body,labels",
    ])
    issues = json.loads(issues_json)

    updated = 0
    for issue in issues:
        to_add = build_labels(issue)
        if not to_add:
            continue
        cmd = ["gh", "issue", "edit", str(issue["number"])]
        for label in to_add:
            cmd.extend(["--add-label", label])
        run(cmd)
        updated += 1

    print(f"Updated issues: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
