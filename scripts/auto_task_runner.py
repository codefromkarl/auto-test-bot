import os
import re
import shutil
import subprocess
import textwrap
import time
from pathlib import Path

# 配置
REPO_ROOT = Path(__file__).resolve().parents[1]
AI_DIR = REPO_ROOT / ".ai"
ACTIVE_FILE = AI_DIR / "ACTIVE.md"
INDEX_FILE = AI_DIR / "index.md"
ISSUES_DIR = AI_DIR / "issues"
HANDOFF_SIGNAL = AI_DIR / "HANDOFF_SIGNAL"
MAX_DURATION_SECONDS = 1200  # 每个 Agent 会话最多跑 10 分钟（防止上下文溢出）
GEMINI_BIN = os.environ.get("GEMINI_BIN", "gemini")
GEMINI_APPROVAL_MODE = os.environ.get("GEMINI_APPROVAL_MODE", "yolo")
ALLOW_NON_READY = os.environ.get("ALLOW_NON_READY", "1").lower() in {"1", "true", "yes"}


def read_active_task():
    if not ACTIVE_FILE.exists():
        return None
    with open(ACTIVE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    # 简单的状态检查，如果包含 "Status: **Done**" 或 "Status: **Completed**" 则停止
    if "Status: **Done**" in content or "Status: **Completed**" in content:
        print(f"📋 Task completed: {content.split('Status:')[1].strip()}")
        return None
    return content


def extract_issue_path_from_active(content: str) -> Path | None:
    link_match = re.search(r"\((issues/ISSUE-\d+\.md)\)", content)
    if link_match:
        return AI_DIR / link_match.group(1)
    issue_match = re.search(r"\bISSUE-\d+\b", content)
    if issue_match:
        return ISSUES_DIR / f"{issue_match.group(0)}.md"
    return None


def parse_issue_metadata(issue_path: Path) -> dict | None:
    if not issue_path.exists():
        print(f"❌ Issue file not found: {issue_path}")
        return None

    meta = {
        "title": "",
        "type": "",
        "status": "",
        "project_status": "",
        "labels": [],
    }

    with open(issue_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("# Issue"):
                meta["title"] = stripped
                if "[Bug]" in stripped:
                    meta["type"] = "Bug"
                elif "[Task]" in stripped:
                    meta["type"] = "Task"
            elif stripped.startswith("- **Status**:"):
                meta["status"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **Project Status**:"):
                meta["project_status"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("- **Labels**:"):
                labels_text = stripped.split(":", 1)[1].strip()
                meta["labels"] = [label.strip() for label in labels_text.split(",") if label.strip()]

    return meta


def is_issue_authorized(meta: dict, allow_non_ready: bool) -> bool:
    labels_lower = {label.lower() for label in meta.get("labels", [])}
    if "ai:analysis-only" in labels_lower or "ai:manual-only" in labels_lower:
        return False
    if "ai:auto-fix" not in labels_lower:
        return False
    if meta.get("type") not in {"Bug", "Task"}:
        return False
    if meta.get("status", "").lower() in {"closed"}:
        return False

    project_status = meta.get("project_status", "").lower()
    if project_status in {"closed", "done"}:
        return False
    if not allow_non_ready and project_status != "ready":
        return False

    return True


def find_next_issue_from_index() -> Path | None:
    if not INDEX_FILE.exists():
        print(f"❌ No index file found: {INDEX_FILE}")
        return None

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith("| ["):
                continue
            columns = [col.strip() for col in stripped.strip("|").split("|")]
            if len(columns) < 5:
                continue
            project_status = columns[3].lower()
            if project_status in {"closed", "done"}:
                continue

            link_match = re.search(r"\((issues/ISSUE-\d+\.md)\)", columns[0])
            if not link_match:
                continue
            issue_path = AI_DIR / link_match.group(1)
            meta = parse_issue_metadata(issue_path)
            if meta and is_issue_authorized(meta, allow_non_ready=ALLOW_NON_READY):
                return issue_path

    return None


def build_gemini_prompt(issue_path: Path) -> str:
    issue_rel = issue_path.relative_to(REPO_ROOT).as_posix()
    return textwrap.dedent(
        f"""\
        PURPOSE: 继续处理未完成的 Issue（{issue_path.stem}）
        TASK:
        - 阅读 GEMINI.md、AGENTS.md 与 AI_EXECUTION_PLAYBOOK.md，并严格遵守
        - 阅读 .ai/ACTIVE.md 与 .ai/index.md，确认当前队列与可执行任务
        - 打开 {issue_rel} 并按照 DoD 执行
        - 所有命令/关键日志/产物路径写入 runs/YYYY-MM-DD/run.md
        MODE: auto
        CONTEXT: GEMINI.md AGENTS.md AI_EXECUTION_PLAYBOOK.md .ai/ACTIVE.md .ai/index.md {issue_rel}
        EXPECTED: 完成该 Issue 的可执行范围，并给出清晰的结论与验证结果
        RULES: 全程中文 | 只处理授权 Issue | 发现新问题需新建 Bug 并将当前任务标记为 Blocked
        """
    ).strip()


def run_agent_session():
    """运行一次 Agent 会话"""
    print("🚀 Starting new Agent session...")

    gemini_path = shutil.which(GEMINI_BIN)
    if not gemini_path:
        print(f"❌ gemini CLI not found: {GEMINI_BIN}")
        return

    active_content = read_active_task()
    issue_path = None
    if active_content:
        issue_path = extract_issue_path_from_active(active_content)
        if issue_path:
            meta = parse_issue_metadata(issue_path)
            if not (meta and is_issue_authorized(meta, allow_non_ready=True)):
                print("❌ Active issue is not authorized for auto execution.")
                issue_path = None

    if not issue_path:
        issue_path = find_next_issue_from_index()

    if not issue_path:
        print("🎉 No authorized unfinished issues found. Exiting.")
        return

    prompt = build_gemini_prompt(issue_path)
    cmd = [
        gemini_path,
        "--prompt",
        prompt,
        "--approval-mode",
        GEMINI_APPROVAL_MODE,
    ]

    process = subprocess.Popen(cmd, cwd=REPO_ROOT.as_posix())

    start_time = time.time()
    while True:
        # 1. 检查任务是否完成
        if process.poll() is not None:
            print("✅ Agent process finished.")
            break

        # 2. 检查是否超时（上下文即将溢出）
        if time.time() - start_time > MAX_DURATION_SECONDS:
            print("⚠️ Context limit approaching. Forcing restart...")
            process.terminate()
            break

        # 3. 检查是否有主动交接信号
        if HANDOFF_SIGNAL.exists():
            print("🔄 Handoff signal received. Restarting...")
            HANDOFF_SIGNAL.unlink()
            process.terminate()
            break

        time.sleep(5)


def main():
    print("🤖 Auto-Task Runner Started")
    print(f"Monitoring {ACTIVE_FILE}...")

    session_count = 0
    while True:
        task = read_active_task()
        if not task:
            print("🎉 No active tasks or task completed. Exiting.")
            break

        session_count += 1
        print(f"\n--- Session #{session_count} ---")
        run_agent_session()

        # 休息一下，避免死循环太快
        time.sleep(2)


if __name__ == "__main__":
    main()
