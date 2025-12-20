"""
Codex Bridge Script for Claude Agent Skills.
Wraps the Codex CLI to provide a JSON-based interface for Claude.
"""
from __future__ import annotations

import json
import re
import os
import queue
import subprocess
import threading
import time
import shutil
import argparse
import selectors
import fcntl
import sys
from typing import Generator, List, Optional

def run_shell_command(cmd: List[str]) -> Generator[str, None, None]:
    """Execute a command and stream its output line-by-line."""
    popen_cmd = cmd.copy()
    # Resolve executable path
    codex_path = shutil.which('codex') or cmd[0]
    popen_cmd[0] = codex_path

    process = subprocess.Popen(
        popen_cmd,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding='utf-8',
    )

    output_queue: queue.Queue[Optional[str]] = queue.Queue()
    GRACEFUL_SHUTDOWN_DELAY = 0.3

    def is_turn_completed(line: str) -> bool:
        """更健壮的完成检测，使用正则提取JSON"""
        # 首先尝试直接解析
        try:
            data = json.loads(line)
            return data.get("type") == "turn.completed"
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

        # 如果直接解析失败，尝试从行中提取JSON
        try:
            match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', line)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data.get("type") == "turn.completed"
        except:
            pass

        return False

    def extract_json_from_line(line: str) -> Optional[dict]:
        """从行中提取JSON数据，处理混合输出"""
        try:
            # 首先尝试直接解析
            return json.loads(line)
        except json.JSONDecodeError:
            pass

        # 尝试正则提取JSON
        match = re.search(r'(\{.*\})', line)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        return None

    def extract_json_from_line(line: str) -> Optional[dict]:
        """从行中提取JSON数据，处理混合输出"""
        try:
            # 首先尝试直接解析
            return json.loads(line)
        except json.JSONDecodeError:
            pass

        # 尝试正则提取JSON
        match = re.search(r'(\{.*\})', line)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        return None

    def read_output() -> None:
        """非阻塞读取输出，避免line-by-line阻塞"""
        if not process.stdout:
            output_queue.put(None)
            return

        # 设置非阻塞模式（仅Unix）
        try:
            fd = process.stdout.fileno()
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        except (AttributeError, OSError):
            # Windows或其他不支持fcntl的系统，回退到阻塞模式
            pass

        buffer = ""
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)

        while True:
            # 检查进程是否已经结束
            if process.poll() is not None:
                # 读取剩余数据
                try:
                    remaining = process.stdout.read()
                    if remaining:
                        buffer += remaining
                except:
                    pass
                break

            # 使用selector等待数据，超时1秒
            events = selector.select(timeout=1)
            if not events:
                continue

            for event in events:
                try:
                    data = event.fileobj.read(4096)
                    if not data:
                        break
                    buffer += data

                    # 处理完整行
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        stripped = line.strip()
                        if stripped:
                            output_queue.put(stripped)

                            # 检查是否完成，但不立即终止
                            if is_turn_completed(stripped):
                                # 等待更多数据，然后优雅退出
                                time.sleep(GRACEFUL_SHUTDOWN_DELAY)
                                selector.close()
                                return
                except:
                    break

        # 处理缓冲区中剩余的数据
        if buffer.strip():
            output_queue.put(buffer.strip())

        selector.close()
        output_queue.put(None)

    thread = threading.Thread(target=read_output)
    thread.start()

    while True:
        try:
            line = output_queue.get(timeout=0.5)
            if line is None:
                break
            yield line
        except queue.Empty:
            if process.poll() is not None and not thread.is_alive():
                break

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    thread.join(timeout=5)

    while not output_queue.empty():
        try:
            line = output_queue.get_nowait()
            if line is not None:
                yield line
        except queue.Empty:
            break

def windows_escape(prompt):
    """Windows style string escaping."""
    result = prompt.replace('\\', '\\\\')
    result = result.replace('"', '\\"')
    result = result.replace('\n', '\\n')
    result = result.replace('\r', '\\r')
    result = result.replace('\t', '\\t')
    result = result.replace('\b', '\\b')
    result = result.replace('\f', '\\f')
    result = result.replace("'", "\\'")
    return result

def main():
    parser = argparse.ArgumentParser(description="Codex Bridge")
    parser.add_argument("--PROMPT", required=True, help="Instruction for the task to send to codex.")
    parser.add_argument("--cd", required=True, help="Set the workspace root for codex before executing the task.")
    parser.add_argument("--sandbox", default="read-only", choices=["read-only", "workspace-write", "danger-full-access"], help="Sandbox policy for model-generated commands. Defaults to `read-only`.")
    parser.add_argument("--SESSION_ID", default="", help="Resume the specified session of the codex. Defaults to `None`, start a new session.")
    parser.add_argument("--skip-git-repo-check", action="store_true", default=True, help="Allow codex running outside a Git repository (useful for one-off directories).")
    parser.add_argument("--return-all-messages", action="store_true", help="Return all messages (e.g. reasoning, tool calls, etc.) from the codex session. Set to `False` by default, only the agent's final reply message is returned.")
    parser.add_argument("--image", action="append", default=[], help="Attach one or more image files to the initial prompt. Separate multiple paths with commas or repeat the flag.")
    parser.add_argument("--model", default="", help="The model to use for the codex session. This parameter is strictly prohibited unless explicitly specified by the user.")
    parser.add_argument("--yolo", action="store_true", help="Run every command without approvals or sandboxing. Only use when `sandbox` couldn't be applied.")
    parser.add_argument("--profile", default="", help="Configuration profile name to load from `~/.codex/config.toml`. This parameter is strictly prohibited unless explicitly specified by the user.")

    args = parser.parse_args()

    cmd = ["codex", "exec", "--sandbox", args.sandbox, "--cd", args.cd, "--json"]

    if args.image:
        cmd.extend(["--image", ",".join(args.image)])

    if args.model:
        cmd.extend(["--model", args.model])

    if args.profile:
        cmd.extend(["--profile", args.profile])

    if args.yolo:
        cmd.append("--yolo")

    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")

    if args.SESSION_ID:
        cmd.extend(["resume", args.SESSION_ID])

    PROMPT = args.PROMPT
    if os.name == "nt":
        PROMPT = windows_escape(PROMPT)

    cmd += ['--', PROMPT]

    # Execution Logic
    all_messages = []
    agent_messages = ""
    success = True
    err_message = ""
    thread_id = None

    for line in run_shell_command(cmd):
        try:
            # 使用更健壮的JSON提取
            line_dict = extract_json_from_line(line.strip())
            if not line_dict:
                # 如果无法解析为JSON，保存为原始文本
                line_dict = {"type": "raw_output", "content": line.strip()}

            all_messages.append(line_dict)
            item = line_dict.get("item", {})
            item_type = item.get("type", "")
            if item_type == "agent_message":
                agent_messages = agent_messages + item.get("text", "")
            if line_dict.get("thread_id") is not None:
                thread_id = line_dict.get("thread_id")
            if "fail" in line_dict.get("type", ""):
                success = False if len(agent_messages) == 0 else success
                err_message += "\n\n[codex error] " + line_dict.get("error", {}).get("message", "")
            if "error" in line_dict.get("type", ""):
                error_msg = line_dict.get("message", "")
                is_reconnecting = bool(re.match(r'^Reconnecting\.\.\.\s+\d+/\d+$', error_msg))

                if not is_reconnecting:
                    success = False if len(agent_messages) == 0 else success
                    err_message += "\n\n[codex error] " + error_msg

        except json.JSONDecodeError:
            err_message += "\n\n[json decode error] " + line
            continue

        except Exception as error:
            err_message += "\n\n[unexpected error] " + f"Unexpected error: {error}. Line: {line!r}"
            success = False
            break

    if thread_id is None:
        success = False
        err_message = "Failed to get `SESSION_ID` from the codex session. \n\n" + err_message

    if len(agent_messages) == 0:
        success = False
        err_message = "Failed to get `agent_messages` from the codex session. \n\n You can try to set `return_all_messages` to `True` to get the full reasoning information. " + err_message

    if success:
        result = {
            "success": True,
            "SESSION_ID": thread_id,
            "agent_messages": agent_messages,
        }

    else:
        result = {"success": False, "error": err_message}

    if args.return_all_messages:
        result["all_messages"] = all_messages

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
