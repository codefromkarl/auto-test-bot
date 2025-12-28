# Keyword DSL Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a keyword-style DSL that compiles to existing Workflow/Phase/Action and runs on WorkflowExecutor, while keeping selectors/timeouts out of the DSL and enabling plugin keywords.

**Architecture:** A line-based DSL parser builds an AST, a compiler maps AST statements to core actions or plugin actions, and the existing executor runs the compiled workflow. Locator packs resolve locator keys to selectors at compile time or just-in-time.

**Tech Stack:** Python 3, existing `src/models/*`, `src/executor/workflow_executor.py`, unit tests with pytest.

## Task 1: Add Keyword DSL AST + Parser (minimal core)

**Files:**
- Create: `src/keyword_dsl/__init__.py`
- Create: `src/keyword_dsl/ast.py`
- Create: `src/keyword_dsl/parser.py`
- Test: `tests/unit/test_keyword_dsl_parser.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_dsl_parser.py
import pytest
from keyword_dsl.parser import parse_dsl


def test_parse_minimal_case():
    dsl = """
CASE "DEMO"
  STEP open url="https://example.com"
  STEP click target="nav.ai_create"
END
"""
    ast = parse_dsl(dsl, source_path="demo.dsl")
    assert ast.cases[0].name == "DEMO"
    assert ast.cases[0].statements[0].keyword == "open"
    assert ast.cases[0].statements[1].params["target"] == "nav.ai_create"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_dsl_parser.py::test_parse_minimal_case -v`
Expected: FAIL with `ModuleNotFoundError: keyword_dsl` or `parse_dsl` missing.

**Step 3: Write minimal implementation**

```python
# src/keyword_dsl/ast.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SourceRef:
    path: str
    line: int
    column: int = 1


@dataclass
class DslStatement:
    kind: str  # "step" or "assert"
    keyword: str
    params: Dict[str, str]
    source: SourceRef


@dataclass
class DslCase:
    name: str
    source: SourceRef
    tags: List[str] = field(default_factory=list)
    locator_pack: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    statements: List[DslStatement] = field(default_factory=list)


@dataclass
class DslFile:
    cases: List[DslCase]
    source_path: str
```

```python
# src/keyword_dsl/parser.py
import json
import re
import shlex
from typing import List
from .ast import DslFile, DslCase, DslStatement, SourceRef


class DslParseError(ValueError):
    pass


_CASE_RE = re.compile(r'^CASE\s+"(?P<name>.+)"\s*$')
_TAGS_RE = re.compile(r'^TAGS\s+(?P<json>\[.*\])\s*$')
_LOCATORS_RE = re.compile(r'^USE_LOCATORS\s+"(?P<name>.+)"\s*$')
_VAR_RE = re.compile(r'^VAR\s+(?P<name>\w+)\s*=\s*"(?P<value>.*)"\s*$')


def parse_dsl(text: str, source_path: str = "<memory>") -> DslFile:
    cases: List[DslCase] = []
    current: DslCase | None = None

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line == "END":
            if not current:
                raise DslParseError(f"END without CASE at {source_path}:{idx}")
            cases.append(current)
            current = None
            continue

        m = _CASE_RE.match(line)
        if m:
            if current:
                raise DslParseError(f"Nested CASE at {source_path}:{idx}")
            current = DslCase(name=m.group("name"), source=SourceRef(source_path, idx))
            continue

        if not current:
            raise DslParseError(f"Line outside CASE at {source_path}:{idx}")

        m = _TAGS_RE.match(line)
        if m:
            current.tags = json.loads(m.group("json"))
            continue

        m = _LOCATORS_RE.match(line)
        if m:
            current.locator_pack = m.group("name")
            continue

        m = _VAR_RE.match(line)
        if m:
            current.variables[m.group("name")] = m.group("value")
            continue

        tokens = shlex.split(line)
        if not tokens:
            continue
        head = tokens[0]
        if head in {"STEP", "ASSERT"}:
            if len(tokens) < 2:
                raise DslParseError(f"Missing keyword at {source_path}:{idx}")
            keyword = tokens[1]
            params = {}
            for token in tokens[2:]:
                if "=" not in token:
                    raise DslParseError(f"Invalid param '{token}' at {source_path}:{idx}")
                key, value = token.split("=", 1)
                params[key] = value
            current.statements.append(
                DslStatement(
                    kind="step" if head == "STEP" else "assert",
                    keyword=keyword,
                    params=params,
                    source=SourceRef(source_path, idx),
                )
            )
            continue

        raise DslParseError(f"Unknown line '{line}' at {source_path}:{idx}")

    if current:
        raise DslParseError(f"Missing END for CASE {current.name} at {source_path}")

    return DslFile(cases=cases, source_path=source_path)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_dsl_parser.py::test_parse_minimal_case -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/keyword_dsl/__init__.py src/keyword_dsl/ast.py src/keyword_dsl/parser.py tests/unit/test_keyword_dsl_parser.py
git commit -m "feat: add keyword DSL AST and parser"
```

## Task 2: Keyword Registry (core keywords + validation)

**Files:**
- Create: `src/keyword_dsl/registry.py`
- Test: `tests/unit/test_keyword_registry.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_registry.py
import pytest
from keyword_dsl.registry import KeywordRegistry, KeywordSpec


def test_registry_validates_required_params():
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    spec = registry.get("open")
    with pytest.raises(ValueError):
        spec.validate({})
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_registry.py::test_registry_validates_required_params -v`
Expected: FAIL (registry not found)

**Step 3: Write minimal implementation**

```python
# src/keyword_dsl/registry.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeywordSpec:
    name: str
    action: str
    required_params: List[str] = field(default_factory=list)
    is_plugin: bool = False
    plugin_name: Optional[str] = None

    def validate(self, params: Dict[str, str]) -> None:
        missing = [p for p in self.required_params if p not in params]
        if missing:
            raise ValueError(f"Missing params for {self.name}: {missing}")


class KeywordRegistry:
    def __init__(self):
        self._specs: Dict[str, KeywordSpec] = {}

    def register(self, spec: KeywordSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Duplicate keyword: {spec.name}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> KeywordSpec:
        if name not in self._specs:
            raise ValueError(f"Unknown keyword: {name}")
        return self._specs[name]

    def has(self, name: str) -> bool:
        return name in self._specs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_registry.py::test_registry_validates_required_params -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/keyword_dsl/registry.py tests/unit/test_keyword_registry.py
git commit -m "feat: add keyword registry with validation"
```

## Task 3: Locator Pack Registry (resolve locator keys to selectors)

**Files:**
- Create: `src/keyword_dsl/locator_packs.py`
- Test: `tests/unit/test_keyword_locator_packs.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_locator_packs.py
from keyword_dsl.locator_packs import LocatorPackRegistry


def test_resolve_locator_key():
    packs = LocatorPackRegistry({"demo": {"nav.ai_create": "#nav-ai"}})
    assert packs.resolve("demo", "nav.ai_create") == "#nav-ai"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_locator_packs.py::test_resolve_locator_key -v`
Expected: FAIL (registry missing)

**Step 3: Write minimal implementation**

```python
# src/keyword_dsl/locator_packs.py
from typing import Dict


class LocatorPackRegistry:
    def __init__(self, packs: Dict[str, Dict[str, str]]):
        self._packs = packs

    def resolve(self, pack: str, key: str) -> str:
        if pack not in self._packs:
            raise ValueError(f"Unknown locator pack: {pack}")
        mapping = self._packs[pack]
        if key not in mapping:
            raise ValueError(f"Unknown locator key: {key}")
        return mapping[key]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_locator_packs.py::test_resolve_locator_key -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/keyword_dsl/locator_packs.py tests/unit/test_keyword_locator_packs.py
git commit -m "feat: add locator pack registry"
```

## Task 4: Compiler (DSL -> Workflow)

**Files:**
- Create: `src/keyword_dsl/compiler.py`
- Test: `tests/unit/test_keyword_dsl_compiler.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_dsl_compiler.py
from keyword_dsl.ast import DslCase, DslStatement, SourceRef
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case


def test_compile_core_steps():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        locator_pack="demo",
        statements=[
            DslStatement("step", "open", {"url": "https://example.com"}, SourceRef("demo.dsl", 2)),
            DslStatement("step", "click", {"target": "nav.ai_create"}, SourceRef("demo.dsl", 3)),
        ],
    )
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    registry.register(KeywordSpec(name="click", action="click", required_params=["target"]))
    packs = LocatorPackRegistry({"demo": {"nav.ai_create": "#nav-ai"}})

    workflow = compile_case(case, registry, packs)
    steps = workflow.phases[0].steps
    assert steps[0].get_step_name() == "open_page"
    assert steps[1].params["selector"] == "#nav-ai"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_dsl_compiler.py::test_compile_core_steps -v`
Expected: FAIL (compiler missing)

**Step 3: Write minimal implementation**

```python
# src/keyword_dsl/compiler.py
from typing import Dict
from models import Workflow
from models.phase import Phase
from models.action import Action
from .ast import DslCase
from .registry import KeywordRegistry
from .locator_packs import LocatorPackRegistry


def compile_case(case: DslCase, registry: KeywordRegistry, packs: LocatorPackRegistry) -> Workflow:
    workflow = Workflow(name=case.name)
    phase = Phase(name="main")

    for stmt in case.statements:
        spec = registry.get(stmt.keyword)
        spec.validate(stmt.params)

        params: Dict[str, str] = dict(stmt.params)
        if "target" in params:
            if not case.locator_pack:
                raise ValueError("locator_pack is required when using target")
            params["selector"] = packs.resolve(case.locator_pack, params.pop("target"))

        action = Action.create(spec.action, params)
        phase.add_step(action)

    workflow.add_phase(phase)
    return workflow
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_dsl_compiler.py::test_compile_core_steps -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/keyword_dsl/compiler.py tests/unit/test_keyword_dsl_compiler.py
git commit -m "feat: compile keyword DSL to workflow"
```

## Task 5: Plugin Keyword Support (keyword -> plugin_action)

**Files:**
- Modify: `src/models/action.py`
- Modify: `src/executor/workflow_executor.py`
- Test: `tests/unit/test_keyword_dsl_plugin_keyword.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_dsl_plugin_keyword.py
from keyword_dsl.ast import DslCase, DslStatement, SourceRef
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case


def test_compile_plugin_keyword():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        statements=[
            DslStatement("step", "aigc.generate", {"mode": "storyboard"}, SourceRef("demo.dsl", 2)),
        ],
    )
    registry = KeywordRegistry()
    registry.register(
        KeywordSpec(name="aigc.generate", action="plugin_action", required_params=["mode"], is_plugin=True, plugin_name="aigc")
    )
    packs = LocatorPackRegistry({})

    workflow = compile_case(case, registry, packs)
    assert workflow.phases[0].steps[0].get_step_name() == "plugin_action"
    assert workflow.phases[0].steps[0].params["plugin"] == "aigc"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_dsl_plugin_keyword.py::test_compile_plugin_keyword -v`
Expected: FAIL (plugin_action not supported)

**Step 3: Write minimal implementation**

```python
# src/models/action.py (add class)
class PluginAction(Action):
    def get_step_name(self) -> str:
        return "plugin_action"

    def execute(self, context: Context) -> Context:
        return context
```

```python
# src/models/action.py (extend Action.create)
        action_classes = {
            # existing...
            'save_data': SaveDataAction,
            'plugin_action': PluginAction,
        }
```

```python
# src/keyword_dsl/compiler.py (extend)
        if spec.is_plugin:
            params = {"plugin": spec.plugin_name, "keyword": spec.name, **stmt.params}
            action = Action.create("plugin_action", params)
        else:
            # existing core mapping
```

```python
# src/executor/workflow_executor.py (minimal hook)
# inside execute_single_action or action dispatch
if action_name == "plugin_action":
    plugin_name = params.get("plugin")
    if not self.plugin_manager:
        return {"success": False, "error": "plugin manager not configured"}
    result = await self.plugin_manager.execute_plugin(plugin_name, params)
    return {"success": True, "context": {"plugin_result": result}}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_dsl_plugin_keyword.py::test_compile_plugin_keyword -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/action.py src/keyword_dsl/compiler.py src/executor/workflow_executor.py tests/unit/test_keyword_dsl_plugin_keyword.py
git commit -m "feat: support plugin keywords"
```

## Task 6: DSL Entry Point (parse -> compile -> execute)

**Files:**
- Create: `src/main_keyword_dsl.py`
- Test: `tests/unit/test_keyword_dsl_entrypoint.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_dsl_entrypoint.py
from keyword_dsl.ast import DslCase, DslStatement, SourceRef, DslFile
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case


def test_entrypoint_compiles_case():
    case = DslCase(
        name="DEMO",
        source=SourceRef("demo.dsl", 1),
        statements=[DslStatement("step", "open", {"url": "https://example.com"}, SourceRef("demo.dsl", 2))],
    )
    registry = KeywordRegistry()
    registry.register(KeywordSpec(name="open", action="open_page", required_params=["url"]))
    packs = LocatorPackRegistry({})
    workflow = compile_case(case, registry, packs)
    assert workflow.name == "DEMO"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_dsl_entrypoint.py::test_entrypoint_compiles_case -v`
Expected: FAIL (entrypoint missing)

**Step 3: Write minimal implementation**

```python
# src/main_keyword_dsl.py
import argparse
from keyword_dsl.parser import parse_dsl
from keyword_dsl.registry import KeywordRegistry, KeywordSpec
from keyword_dsl.locator_packs import LocatorPackRegistry
from keyword_dsl.compiler import compile_case
from executor import WorkflowExecutor
from browser_manager import BrowserManager
from utils import ConfigLoader, setup_logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsl", required=True)
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    config = ConfigLoader(args.config).load_config()
    setup_logging(config.get("logging", {}))

    text = open(args.dsl, "r", encoding="utf-8").read()
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

    # run async executor from sync main
    import asyncio
    asyncio.run(executor.execute_workflow(workflow))


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_dsl_entrypoint.py::test_entrypoint_compiles_case -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/main_keyword_dsl.py tests/unit/test_keyword_dsl_entrypoint.py
git commit -m "feat: add keyword DSL entrypoint"
```

## Task 7: DSL Purity Gate (no selectors/timeouts in DSL)

**Files:**
- Create: `src/keyword_dsl/lint.py`
- Test: `tests/unit/test_keyword_dsl_lint.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_keyword_dsl_lint.py
import pytest
from keyword_dsl.lint import lint_dsl_text


def test_rejects_selector_usage():
    dsl = """
CASE "DEMO"
  STEP click selector="#bad"
END
"""
    errors = lint_dsl_text(dsl)
    assert "selector" in errors[0]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_keyword_dsl_lint.py::test_rejects_selector_usage -v`
Expected: FAIL (lint missing)

**Step 3: Write minimal implementation**

```python
# src/keyword_dsl/lint.py
FORBIDDEN_TOKENS = {"selector=", "timeout=", "sleep"}


def lint_dsl_text(text: str) -> list[str]:
    errors: list[str] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for token in FORBIDDEN_TOKENS:
            if token in line:
                errors.append(f"Line {idx}: forbidden token '{token}'")
    return errors
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_keyword_dsl_lint.py::test_rejects_selector_usage -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/keyword_dsl/lint.py tests/unit/test_keyword_dsl_lint.py
git commit -m "feat: add keyword DSL lint gate"
```

## Task 8: Documentation and Example DSL

**Files:**
- Create: `docs/keyword_dsl/README.md`
- Create: `examples/keyword_dsl/demo.dsl`

**Step 1: Add documentation**

```markdown
# Keyword DSL

- Each file contains one or more CASE blocks
- Only keyword lines are allowed (STEP/ASSERT/VAR/TAGS/USE_LOCATORS)
- No selectors or timeouts in DSL

Example:

CASE "DEMO"
  TAGS ["example"]
  USE_LOCATORS "demo"
  STEP open url="https://example.com"
  STEP click target="nav.ai_create"
  ASSERT text_contains target="toast" text="success"
END
```

**Step 2: Add example DSL**

```dsl
CASE "DEMO"
  TAGS ["example"]
  USE_LOCATORS "demo"
  STEP open url="https://example.com"
  STEP click target="nav.ai_create"
END
```

**Step 3: Commit**

```bash
git add docs/keyword_dsl/README.md examples/keyword_dsl/demo.dsl
git commit -m "docs: add keyword DSL overview and example"
```

## Notes
- If plugin execution needs ScenarioContext, wrap params into ScenarioContext inside WorkflowExecutor for plugin_action.
- When adding plugin keywords, require `plugin_name` and explicit keyword naming to avoid collisions.
- Prefer raising `DslParseError` with `source_ref` for all parser/compile errors.
