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


async def main():
    """Main function for workflow execution"""
    parser = argparse.ArgumentParser(description='Workflow-First Auto Test Bot')
    parser.add_argument('--workflow', '-w', required=True, help='Workflow YAML file path')
    parser.add_argument('--config', '-c', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--mcp-diagnostic', action='store_true', help='MCP deep diagnostic mode')
    parser.add_argument('--report-dir', default=None, help='Override report output directory')

    args = parser.parse_args()

    try:
        # Setup logging
        config_loader = ConfigLoader(args.config)
        config = config_loader.load_config()
        setup_logging(config.get('logging', {}))

        logger = logging.getLogger(__name__)

        # Load workflow
        workflow = await load_workflow(args.workflow)
        logger.info(f"Loaded workflow: {workflow.name}")

        # Initialize components
        browser_manager = BrowserManager(config)
        await browser_manager.initialize()

        if args.report_dir:
            config.setdefault('reporting', {})
            config['reporting']['output_dir'] = args.report_dir

        # MCP observation is optional; keep disabled by default for now
        mcp_observer = None

        reporter = DecisionReporter(config)

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
        if result.get('overall_success'):
            print(f"✅ Workflow '{workflow.name}' completed successfully")
        else:
            print(f"❌ Workflow '{workflow.name}' failed: {result.get('error', {}).get('error', 'Unknown error')}")

        # Exit with appropriate code
        sys.exit(0 if result.get('overall_success') else 1)

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

    with open(workflow_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()

    return Workflow.from_yaml(yaml_content)


if __name__ == "__main__":
    # Run main function
    asyncio.run(main())
