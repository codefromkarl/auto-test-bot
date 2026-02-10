#!/usr/bin/env python3
"""
Spec Tree Execution Engine
解决Spec到Workflow执行割裂的核心引擎

核心功能：
1. 解析Spec Registry的树状结构
2. 根据mode选择执行子树
3. 递归执行节点（suite和leaf）
4. 统一聚合evidence和report
"""

import asyncio
import sys
import os
import yaml
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpecExecutionEngine:
    """Spec树执行引擎 - 专注于解决Spec到Workflow的执行割裂"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registry = None

    def load_registry(self, registry_path: str) -> Dict:
        """加载Spec Registry"""
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                self.registry = yaml.safe_load(f)
            self.logger.info(f"Loaded spec registry from {registry_path}")
            return self.registry
        except Exception as e:
            self.logger.error(f"Failed to load registry: {e}")
            raise

    def resolve_spec(self, spec_id: str) -> Dict:
        """解析Spec配置"""
        if not self.registry:
            raise ValueError("Registry not loaded")

        spec_config = self.registry.get("spec_registry", {}).get(spec_id)
        if not spec_config:
            raise ValueError(f"Spec not found: {spec_id}")

        return spec_config

    def get_execution_plan(self, spec_config: Dict, mode: str) -> List[str]:
        """根据mode获取执行计划的节点列表"""
        modes = spec_config.get("modes", {})
        mode_config = modes.get(mode)

        if not mode_config:
            raise ValueError(f"Mode not found: {mode}")

        return mode_config.get("include", [])

    def resolve_leaf_to_workflow(self, leaf_id: str, spec_config: Dict) -> str:
        """将leaf节点解析为workflow路径"""
        leaf_tests = spec_config.get("leaf_tests", {})
        leaf_config = leaf_tests.get(leaf_id)

        if not leaf_config:
            raise ValueError(f"Leaf test not found: {leaf_id}")

        executor = leaf_config.get("executor", {})
        if executor.get("kind") != "workflow":
            raise ValueError(f"Leaf {leaf_id} is not a workflow executor")

        workflow_path = executor.get("ref")
        if not workflow_path or not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")

        return workflow_path

    def resolve_node_to_leaf_ids(
        self, node_path: str, root: Dict, spec_config: Dict
    ) -> List[str]:
        """将节点路径解析为leaf ID列表"""
        path_parts = node_path.split(".")
        current = root

        # 导航到目标节点
        for part in path_parts:
            if part == "root":
                continue
            current = current.get(part, {})

        # 如果是leaf节点，直接返回
        if current.get("type") == "test":
            return [current.get("id")]

        # 如果是suite节点，递归解析children
        children = current.get("children", [])
        leaf_ids = []

        for child_id in children:
            child_path = f"{node_path}.{child_id}"
            child_leaf_ids = self.resolve_node_to_leaf_ids(
                child_path, root, spec_config
            )
            leaf_ids.extend(child_leaf_ids)

        return leaf_ids

    async def execute_spec(self, spec_id: str, mode: str) -> Dict:
        """执行Spec的入口点 - 核心逻辑"""
        # 加载和解析Spec
        spec_config = self.resolve_spec(spec_id)

        self.logger.info(f"Executing spec: {spec_id}[{mode}]")

        # 获取执行计划
        target_leaf_ids = self.get_execution_plan(spec_config, mode)
        self.logger.info(f"Execution plan: {target_leaf_ids}")

        # 执行上下文
        context = {
            "spec_id": spec_id,
            "mode": mode,
            "spec_config": spec_config,
            "results": {},
        }

        # 去重并执行 (保持顺序)
        seen = set()
        unique_leaf_ids = [x for x in target_leaf_ids if not (x in seen or seen.add(x))]
        self.logger.info(f"Resolved leaf IDs: {unique_leaf_ids}")

        results = []
        for leaf_id in unique_leaf_ids:
            try:
                workflow_path = self.resolve_leaf_to_workflow(leaf_id, spec_config)
                result = await self._execute_workflow(workflow_path, leaf_id, context)
                results.append(result)
            except Exception as e:
                error_result = {
                    "leaf_id": leaf_id,
                    "workflow_path": f"NOT_FOUND: {leaf_id}",
                    "success": False,
                    "error": str(e),
                    "duration_sec": 0,
                }
                results.append(error_result)
                self.logger.error(f"Failed to execute {leaf_id}: {e}")

        # 聚合结果
        return self._aggregate_results(spec_id, mode, results, context)

    async def _execute_workflow(
        self, workflow_path: str, leaf_id: str, context: Dict
    ) -> Dict:
        """执行单个workflow"""
        start_time = datetime.now()

        try:
            self.logger.info(f"Executing workflow: {workflow_path} (leaf: {leaf_id})")

            # 构造执行命令
            cmd = [sys.executable, "src/main_workflow.py", "--workflow", workflow_path]

            # 执行workflow
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30分钟超时
            )

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "leaf_id": leaf_id,
                "workflow_path": workflow_path,
                "success": result.returncode == 0,
                "duration_sec": duration,
                "stdout": result.stdout[-1000:]
                if result.stdout
                else "",  # 限制输出长度
                "stderr": result.stderr[-1000:] if result.stderr else "",
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "leaf_id": leaf_id,
                "workflow_path": workflow_path,
                "success": False,
                "duration_sec": (datetime.now() - start_time).total_seconds(),
                "error": "TIMEOUT",
            }
        except Exception as e:
            return {
                "leaf_id": leaf_id,
                "workflow_path": workflow_path,
                "success": False,
                "duration_sec": (datetime.now() - start_time).total_seconds(),
                "error": str(e),
            }

    def _aggregate_results(
        self, spec_id: str, mode: str, results: List[Dict], context: Dict
    ) -> Dict:
        """聚合执行结果"""
        total_workflows = len(results)
        successful_workflows = sum(1 for r in results if r.get("success"))

        # 生成统一的复现命令
        repro_command = f"python3 src/main_workflow.py --spec {spec_id} --mode {mode}"

        # 生成leaf级别的复现命令
        leaf_repro_commands = {}
        for result in results:
            leaf_id = result.get("leaf_id")
            workflow_path = result.get("workflow_path")
            if workflow_path and not workflow_path.startswith("NOT_FOUND"):
                leaf_repro_commands[leaf_id] = (
                    f"python3 src/main_workflow.py --workflow {workflow_path}"
                )

        return {
            "spec_id": spec_id,
            "mode": mode,
            "overall_success": successful_workflows == total_workflows,
            "summary": {
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "failed_workflows": total_workflows - successful_workflows,
                "success_rate": successful_workflows / total_workflows
                if total_workflows > 0
                else 0,
                "total_duration_sec": sum(r.get("duration_sec", 0) for r in results),
            },
            "repro_command": repro_command,
            "leaf_repro_commands": leaf_repro_commands,
            "workflow_results": results,
            "execution_timestamp": datetime.now().isoformat(),
        }


# CLI接口
async def main():
    parser = argparse.ArgumentParser(description="Spec Tree Execution Engine")
    parser.add_argument("--spec", required=True, help="Spec ID (e.g., NH-SMOKE-001)")
    parser.add_argument(
        "--mode", default="full", help="Execution mode (quick/full/health)"
    )
    parser.add_argument(
        "--registry", default="config/spec_registry.yaml", help="Spec registry file"
    )
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    # 设置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        # 创建执行引擎
        engine = SpecExecutionEngine()

        # 加载registry
        engine.load_registry(args.registry)

        # 执行Spec
        result = await engine.execute_spec(args.spec, args.mode)

        # 输出结果
        print("=" * 60)
        print(f"Spec Execution Results: {args.spec}[{args.mode}]")
        print("=" * 60)

        if result["overall_success"]:
            print(f"✅ OVERALL SUCCESS")
        else:
            print(f"❌ OVERALL FAILURE")

        summary = result["summary"]
        print(f"📊 Summary:")
        print(f"   Total workflows: {summary['total_workflows']}")
        print(f"   Successful: {summary['successful_workflows']}")
        print(f"   Failed: {summary['failed_workflows']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
        print(f"   Total duration: {summary['total_duration_sec']:.1f}s")

        print(f"\n🔁 Overall repro command:")
        print(f"   {result['repro_command']}")

        if not result["overall_success"]:
            print(f"\n❌ Failed workflows:")
            for wf_result in result["workflow_results"]:
                if not wf_result.get("success"):
                    leaf_id = wf_result.get("leaf_id", "unknown")
                    error = wf_result.get(
                        "error", wf_result.get("stderr", "Unknown error")
                    )
                    print(f"   - {leaf_id}: {error}")

                    # 输出leaf级别的复现命令
                    leaf_commands = result.get("leaf_repro_commands", {})
                    if leaf_id in leaf_commands:
                        print(f"     Repro: {leaf_commands[leaf_id]}")

        # 保存详细报告
        report_path = f"reports/spec_{args.spec}_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("reports", exist_ok=True)

        import json

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 Detailed report saved to: {report_path}")
        print("=" * 60)

        sys.exit(0 if result["overall_success"] else 1)

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
