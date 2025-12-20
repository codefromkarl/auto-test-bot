#!/usr/bin/env python3
"""
执行workflow测试脚本
支持分阶段、并行、批量执行
"""

import os
import sys
import argparse
import asyncio
import subprocess
import time
import threading
import selectors
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import yaml

def load_process_timeout_seconds(config_path: str, explicit_timeout: int = None) -> int:
    """
    计算单个 workflow 子进程的最大允许时长（秒）。

    目标：不要用过短的子进程 timeout 误杀正常流程；真正的“卡住”由执行器的
    execution.max_step_duration_ms / max_wait_for_timeout_ms 控制。
    """
    if explicit_timeout is not None:
        return int(explicit_timeout)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        exec_cfg = cfg.get('execution', {}) if isinstance(cfg, dict) else {}
        max_step_ms = int(exec_cfg.get('max_step_duration_ms', 240000))
        # 每步最多 4 分钟 + 缓冲 1 分钟；再乘以 10 允许较多步骤的 workflow 运行
        base = max(300, int(max_step_ms / 1000) + 60)
        return int(exec_cfg.get('process_timeout_s', base * 10))
    except Exception:
        return 1800  # 30分钟兜底

def find_workflows(workflow_type: str, batch: int = None, base_dir: str = 'workflows') -> List[Path]:
    """查找指定类型的workflow文件"""
    workflows = []
    base = Path(base_dir)

    if workflow_type == 'AT':
        workflows_dir = base / 'at'
        if workflows_dir.exists():
            workflows = list(workflows_dir.glob('*.yaml'))
    elif workflow_type == 'FC':
        workflows_dir = base / 'fc'
        if workflows_dir.exists():
            all_workflows = sorted(workflows_dir.glob('*.yaml'))

            # 如果指定了批次，进行分割
            if batch:
                total = len(all_workflows)
                batch_size = total // 3 + 1  # 分成3批
                start = (batch - 1) * batch_size
                end = start + batch_size
                workflows = all_workflows[start:end]
            else:
                workflows = all_workflows
    elif workflow_type == 'RT':
        workflows_dir = base / 'rt'
        if workflows_dir.exists():
            workflows = list(workflows_dir.glob('*.yaml'))
    else:
        raise ValueError(f"未知的workflow类型: {workflow_type}")

    return sorted(workflows)

def run_single_workflow(workflow_path: Path, config_path: str, process_timeout_s: int) -> Dict:
    """运行单个workflow"""
    cmd = [
        sys.executable,
        'scripts/run_workflow_test.py',
        '--workflow', str(workflow_path),
        '--config', config_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(process_timeout_s)
        )

        report_dir = None
        for line in (result.stdout or "").splitlines() + (result.stderr or "").splitlines():
            if "Report saved to:" in line:
                report_dir = line.split("Report saved to:", 1)[-1].strip()
        return {
            'file': workflow_path.name,
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'report_dir': report_dir,
            'duration': 0  # TODO: 计算执行时间
        }
    except subprocess.TimeoutExpired:
        return {
            'file': workflow_path.name,
            'success': False,
            'stdout': '',
            'stderr': 'TIMEOUT',
            'duration': int(process_timeout_s)
        }
    except Exception as e:
        return {
            'file': workflow_path.name,
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'duration': 0
        }

def _safe_print(lock: threading.Lock, msg: str) -> None:
    if lock:
        with lock:
            print(msg, flush=True)
    else:
        print(msg, flush=True)

def run_single_workflow_live(
    workflow_path: Path,
    config_path: str,
    process_timeout_s: int,
    *,
    heartbeat_s: int = 15,
    print_lock: threading.Lock | None = None,
) -> Dict:
    """
    运行单个 workflow（实时输出子进程日志）。

    设计目标：
    - 让“卡点”在控制台上立即可见，而不是等 subprocess.run 返回后才看到输出
    - 对长时间无输出的情况打印心跳，辅助判断是否卡住
    - 仍保留 stdout 以便最终汇总/报告
    """
    cmd = [
        sys.executable,
        'scripts/run_workflow_test.py',
        '--workflow', str(workflow_path),
        '--config', config_path
    ]

    env = os.environ.copy()
    name = workflow_path.stem
    prefix = f"[{name}] "

    start = time.monotonic()
    last_heartbeat = start
    stdout_lines: List[str] = []
    report_dir = None

    _safe_print(print_lock, f"{prefix}START cmd={' '.join(cmd)} timeout={process_timeout_s}s")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
    except Exception as e:
        return {
            'file': workflow_path.name,
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'report_dir': None,
            'duration': 0,
        }

    sel = None
    try:
        sel = selectors.DefaultSelector()
        if proc.stdout:
            sel.register(proc.stdout, selectors.EVENT_READ)
    except Exception:
        sel = None

    def emit(line: str) -> None:
        nonlocal report_dir
        stdout_lines.append(line)
        stripped = line.rstrip("\n")
        if stripped:
            _safe_print(print_lock, prefix + stripped)
        if "Report saved to:" in stripped:
            report_dir = stripped.split("Report saved to:", 1)[-1].strip()

    timed_out = False
    try:
        while True:
            now = time.monotonic()
            if process_timeout_s and (now - start) > float(process_timeout_s):
                timed_out = True
                break

            rc = proc.poll()
            if rc is not None and (not proc.stdout):
                break

            if proc.stdout is None:
                break

            if sel is not None:
                events = sel.select(timeout=0.5)
                if events:
                    line = proc.stdout.readline()
                    if line:
                        emit(line)
                    else:
                        if proc.poll() is not None:
                            break
                else:
                    if heartbeat_s and (now - last_heartbeat) >= float(heartbeat_s):
                        _safe_print(print_lock, f"{prefix}... RUNNING elapsed={int(now - start)}s")
                        last_heartbeat = now
            else:
                # 退化模式：阻塞读（无心跳）
                line = proc.stdout.readline()
                if not line:
                    break
                emit(line)

        if timed_out:
            _safe_print(print_lock, f"{prefix}TIMEOUT elapsed={int(time.monotonic() - start)}s, terminating...")
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    finally:
        try:
            if sel is not None and proc.stdout is not None:
                sel.unregister(proc.stdout)
        except Exception:
            pass

    # drain remaining output
    try:
        if proc.stdout:
            for line in proc.stdout.readlines():
                if line:
                    emit(line)
    except Exception:
        pass

    try:
        rc = proc.wait(timeout=5)
    except Exception:
        rc = proc.poll()

    duration = time.monotonic() - start
    success = (rc == 0) and (not timed_out)
    _safe_print(print_lock, f"{prefix}END rc={rc} success={success} duration={duration:.1f}s")

    stderr_summary = ''
    if timed_out:
        stderr_summary = 'TIMEOUT'
    elif not success:
        tail = ''.join(stdout_lines[-20:]).strip()
        stderr_summary = tail or 'FAILED'

    return {
        'file': workflow_path.name,
        'success': success,
        'stdout': ''.join(stdout_lines),
        'stderr': stderr_summary,
        'report_dir': report_dir,
        'duration': duration,
    }


def run_parallel(
    workflows: List[Path],
    config_path: str,
    process_timeout_s: int,
    max_workers: int = 4,
    *,
    live: bool = True,
    heartbeat_s: int = 15,
) -> List[Dict]:
    """并行运行workflows"""
    print(f"并行执行 {len(workflows)} 个workflow，最大并发数: {max_workers}", flush=True)

    results = []
    print_lock = threading.Lock() if live else None
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_single_workflow_live if live else run_single_workflow,
                wf,
                config_path,
                process_timeout_s,
                **(
                    {"heartbeat_s": heartbeat_s, "print_lock": print_lock}
                    if live
                    else {}
                ),
            )
            for wf in workflows
        ]

        for future in futures:
            result = future.result()
            results.append(result)

            # 实时输出结果
            status = "✓" if result['success'] else "✗"
            print(f"  {status} {result['file']} (duration={result.get('duration', 0):.1f}s)", flush=True)

    return results

def run_serial(
    workflows: List[Path],
    config_path: str,
    process_timeout_s: int,
    *,
    live: bool = True,
    heartbeat_s: int = 15,
) -> List[Dict]:
    """串行运行workflows"""
    print(f"串行执行 {len(workflows)} 个workflow", flush=True)

    results = []
    for workflow in workflows:
        print(f"\n执行: {workflow.name}", flush=True)
        if live:
            result = run_single_workflow_live(
                workflow,
                config_path,
                process_timeout_s,
                heartbeat_s=heartbeat_s,
                print_lock=None,
            )
        else:
            result = run_single_workflow(workflow, config_path, process_timeout_s)
        results.append(result)

        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result['file']} (duration={result.get('duration', 0):.1f}s)", flush=True)

    return results

def generate_summary(results: List[Dict], workflow_type: str) -> Dict:
    """生成执行摘要"""
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    return {
        'type': workflow_type,
        'total': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': f"{pass_rate:.1f}%",
        'failures': [r for r in results if not r['success']]
    }

def save_report(results: List[Dict], workflow_type: str, batch: int = None) -> None:
    """保存测试报告"""
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_suffix = f"_batch{batch}" if batch else ""
    report_name = f"{workflow_type.lower()}_report{batch_suffix}_{timestamp}.json"
    report_path = Path(f"test_reports/{report_name}")

    report_path.parent.mkdir(exist_ok=True)

    report = {
        'timestamp': timestamp,
        'workflow_type': workflow_type,
        'batch': batch,
        'summary': generate_summary(results, workflow_type),
        'details': results
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n报告已保存到: {report_path}", flush=True)

def main():
    parser = argparse.ArgumentParser(description='执行workflow测试')
    parser.add_argument('--type', choices=['AT', 'FC', 'RT'], required=True,
                      help='要执行的workflow类型')
    parser.add_argument('--config', default='config/config.yaml',
                      help='配置文件路径')
    parser.add_argument('--process-timeout', type=int, default=None,
                      help='单个 workflow 子进程最大时长（秒），不传则从 config.execution 推导')
    parser.add_argument('--parallel', action='store_true',
                      help='并行执行')
    parser.add_argument('--serial', action='store_true',
                      help='串行执行')
    parser.add_argument('--batch', type=int,
                      help='批次号（用于FC并行分批）')
    parser.add_argument('--workers', type=int, default=4,
                      help='最大并发数（默认4）')
    parser.add_argument('--no-live', dest='live', action='store_false',
                      help='关闭实时输出（回退为 capture_output，输出仅在用例结束后可见）')
    parser.set_defaults(live=True)
    parser.add_argument('--heartbeat', type=int, default=15,
                      help='实时输出心跳间隔（秒，默认15；0表示关闭心跳）')

    args = parser.parse_args()

    print("=" * 60, flush=True)
    print(f"执行 {args.type} 系列workflow测试", flush=True)
    print("=" * 60, flush=True)

    # 查找workflows
    workflows = find_workflows(args.type, args.batch)

    if not workflows:
        print(f"未找到 {args.type} 类型的workflow文件", flush=True)
        return

    print(f"找到 {len(workflows)} 个文件:", flush=True)
    for wf in workflows:
        print(f"  - {wf.name}", flush=True)

    # 执行测试
    process_timeout_s = load_process_timeout_seconds(args.config, args.process_timeout)
    print(f"单个 workflow 子进程超时: {process_timeout_s}s", flush=True)
    if args.parallel:
        results = run_parallel(
            workflows,
            args.config,
            process_timeout_s,
            args.workers,
            live=bool(args.live),
            heartbeat_s=int(args.heartbeat),
        )
    else:
        results = run_serial(
            workflows,
            args.config,
            process_timeout_s,
            live=bool(args.live),
            heartbeat_s=int(args.heartbeat),
        )

    # 生成报告
    save_report(results, args.type, args.batch)

    # 输出摘要
    summary = generate_summary(results, args.type)
    print("\n" + "=" * 60, flush=True)
    print("执行摘要:", flush=True)
    print(f"  总数: {summary['total']}", flush=True)
    print(f"  通过: {summary['passed']}", flush=True)
    print(f"  失败: {summary['failed']}", flush=True)
    print(f"  通过率: {summary['pass_rate']}", flush=True)

    if summary['failures']:
        print("\n失败的用例:", flush=True)
        for failure in summary['failures'][:5]:  # 只显示前5个
            print(f"  ✗ {failure['file']}", flush=True)
            if failure['stderr']:
                error = failure['stderr'][:100]
                print(f"    错误: {error}", flush=True)

    print("=" * 60, flush=True)

    # 返回适当的退出码
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == '__main__':
    main()
