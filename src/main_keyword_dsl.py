import argparse
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyword_dsl.parser import parse_dsl
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case
from executor import WorkflowExecutor
from browser_manager import BrowserManager
from utils import ConfigLoader, setup_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsl", required=True)
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    config = ConfigLoader(args.config).load_config()
    setup_logging(config.get("logging", {}))

    with open(args.dsl, "r", encoding="utf-8") as handle:
        text = handle.read()
    ast = parse_dsl(text, source_path=args.dsl)

    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    registry.register(KeywordSpec(name="click", action="click", required_params=["target"]))
    registry.register(KeywordSpec(name="fill", action="input", required_params=["target", "text"]))
    registry.register(KeywordSpec(name="wait", action="wait_for", required_params=["condition"]))

    packs = LocatorPackRegistry(config.get("locator_packs", {}))

    workflow = compile_case(ast.cases[0], registry, packs)

    browser_manager = BrowserManager(config)
    executor = WorkflowExecutor(config, browser_manager)

    asyncio.run(executor.execute_workflow(workflow))


if __name__ == "__main__":
    main()
