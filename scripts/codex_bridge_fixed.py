#!/usr/bin/env python3
"""
简化的Codex Bridge Script - 修复了核心阻塞问题
"""

import json
import subprocess
import sys
import time
import os
import argparse
from typing import Dict, Any


def simple_codex_bridge(prompt: str, workspace: str) -> Dict[str, Any]:
    """简化的Codex桥接器，避免复杂的多线程问题"""

    # 构建codex命令
    cmd = [
        'codex', 'exec',
        '--skip-git-repo-check',
        '--sandbox', 'workspace-write',
        '--cd', workspace,
        '--json',
        '--', prompt
    ]

    print(f"[BRIDGE] Executing: {' '.join(cmd[:4])} ... '{prompt[:50]}...'", file=sys.stderr)

    try:
        # 使用更长的超时和更简单的处理
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时
            cwd=workspace
        )

        print(f"[BRIDGE] Return code: {result.returncode}", file=sys.stderr)
        print(f"[BRIDGE] Stdout length: {len(result.stdout)}", file=sys.stderr)

        if result.stderr:
            print(f"[BRIDGE] Stderr: {result.stderr[:200]}", file=sys.stderr)

        # 尝试解析最后的输出
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):  # 从最后开始找
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'agent_message':
                            return {
                                'success': True,
                                'response': data.get('item', {}).get('text', ''),
                                'thread_id': data.get('thread_id'),
                                'raw_output': result.stdout
                            }
                        elif data.get('type') == 'error':
                            return {
                                'success': False,
                                'error': data.get('message', 'Unknown error'),
                                'raw_output': result.stdout
                            }
                    except json.JSONDecodeError:
                        continue

        # 如果没有找到JSON消息，返回原始输出
        return {
            'success': True,
            'response': result.stdout if result.stdout else 'No output',
            'raw_output': result.stdout
        }

    except subprocess.TimeoutExpired:
        print("[BRIDGE] TIMEOUT - Codex execution timed out", file=sys.stderr)
        return {
            'success': False,
            'error': 'Execution timeout after 120 seconds',
            'raw_output': ''
        }
    except Exception as e:
        print(f"[BRIDGE] ERROR: {e}", file=sys.stderr)
        return {
            'success': False,
            'error': str(e),
            'raw_output': ''
        }


def main():
    parser = argparse.ArgumentParser(description="Simple Codex Bridge")
    parser.add_argument("--PROMPT", required=True, help="Task for codex")
    parser.add_argument("--cd", required=True, help="Working directory")

    args = parser.parse_args()

    # 执行并返回JSON结果
    result = simple_codex_bridge(args.PROMPT, args.cd)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()