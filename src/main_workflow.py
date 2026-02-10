"""
Main entry point for Workflow-First architecture
"""

import asyncio
import logging
import sys
import os
import argparse
from typing import Dict, Any, Optional

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import ConfigLoader, setup_logging
from models import Workflow
from executor import WorkflowExecutor
from browser_manager import BrowserManager
from reporter import DecisionReporter
from reporter.issue_generator import IssueGenerator


async def main():
    """Main function for workflow execution"""
    parser = argparse.ArgumentParser(description="Workflow-First Auto Test Bot")
    parser.add_argument("--workflow", "-w", help="Workflow YAML file path")
    parser.add_argument("--spec", "-s", help="Spec ID for tree-based execution")
    parser.add_argument(
        "--mode", default="full", help="Execution mode for spec (quick/full/health)"
    )
    parser.add_argument(
        "--config", "-c", default="config/config.yaml", help="Configuration file path"
    )
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument(
        "--mcp-diagnostic", action="store_true", help="MCP deep diagnostic mode"
    )
    parser.add_argument(
        "--report-dir", default=None, help="Override report output directory"
    )

    args = parser.parse_args()

    # 检查参数冲突
    if not args.workflow and not args.spec:
        parser.error("Either --workflow or --spec must be provided")
    if args.workflow and args.spec:
        parser.error("Cannot use both --workflow and --spec at the same time")

    # 如果使用--spec，委托给Spec执行引擎
    if args.spec:
        from core.spec_execution_engine import SpecExecutionEngine

        try:
            # 创建执行引擎
            engine = SpecExecutionEngine()

            # 加载registry
            registry_path = os.path.join(
                os.path.dirname(args.config), "spec_registry.yaml"
            )
            engine.load_registry(registry_path)

            # 执行Spec
            result = await engine.execute_spec(args.spec, args.mode)

            # 输出结果
            if result["overall_success"]:
                print(f"✅ Spec {args.spec}[{args.mode}] completed successfully")
            else:
                print(f"❌ Spec {args.spec}[{args.mode}] failed")
                print(f"Success rate: {result['summary']['success_rate']:.1%}")
                print(f"Repro command: {result['repro_command']}")

            # 保存详细报告
            report_dir = args.report_dir or "reports"
            os.makedirs(report_dir, exist_ok=True)

            from datetime import datetime
            import json

            report_path = os.path.join(
                report_dir,
                f"spec_{args.spec}_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            print(f"📄 Detailed report saved to: {report_path}")

            sys.exit(0 if result["overall_success"] else 1)

        except Exception as e:
            if args.debug:
                import traceback

                traceback.print_exc()
            else:
                print(f"Spec execution failed: {e}")
            sys.exit(1)

    try:
        # Setup logging
        config_loader = ConfigLoader(args.config)
        config = config_loader.load_config()
        setup_logging(config.get("logging", {}))

        logger = logging.getLogger(__name__)

        # Load workflow
        workflow = await load_workflow(args.workflow)
        logger.info(f"Loaded workflow: {workflow.name}")

        # Initialize components
        browser_manager = BrowserManager(config)
        await browser_manager.initialize()

        if args.report_dir:
            config.setdefault("reporting", {})
            config["reporting"]["output_dir"] = args.report_dir

        # MCP observation is optional; keep disabled by default for now
        mcp_observer = None

        reporter = DecisionReporter(config)
        issue_gen = IssueGenerator()

        # Create executor
        executor = WorkflowExecutor(config, browser_manager, mcp_observer)

        # Execute workflow
        result = await executor.execute_workflow(workflow)

        # Generate and save report
        report = reporter.generate_report(result)
        saved_files = reporter.save_report(report)

        logger.info("Report generated and saved:")
        for format_type, filepath in saved_files.items():
            logger.info(f"  {format_type.upper()}: {filepath}")

        # Output result
        if result.get("overall_success"):
            print(f"✅ Workflow '{workflow.name}' completed successfully")
        else:
            error_msg = result.get("error", {}).get("error", "Unknown error")
            print(f"❌ Workflow '{workflow.name}' failed: {error_msg}")

            # Auto-generate Issue
            issue_path = issue_gen.generate_issue(workflow.name, result, config)
            if issue_path:
                print(f"📝 Auto-created Issue report: {issue_path}")
                logger.info(f"Auto-created Issue report: {issue_path}")

        # Exit with appropriate code
        sys.exit(0 if result.get("overall_success") else 1)

    except KeyboardInterrupt:
        print("\nUser interrupted execution")
        sys.exit(1)
    except Exception as e:
        print(f"Execution error: {str(e)}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup would be handled by executor
        pass


async def load_workflow(workflow_path: str) -> Workflow:
    """
    Load workflow from file

    Args:
        workflow_path: Path to workflow YAML file

    Returns:
        Loaded workflow
    """
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    with open(workflow_path, "r", encoding="utf-8") as f:
        yaml_content = f.read()

    return Workflow.from_yaml(yaml_content)


if __name__ == "__main__":
    # Run main function
    asyncio.run(main())
