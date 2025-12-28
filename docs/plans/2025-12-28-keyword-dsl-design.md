# Keyword DSL Layer Separation Design

Date: 2025-12-28
Status: Draft
Scope: tool-only, no YAML compatibility, keyword-style DSL

## Goals
- Business layer writes only keyword DSL/Spec, no selectors, no timeouts, no browser details.
- Functional layer owns execution, locator packs, retries, diagnostics, and plugins.
- Support multiple domains via plugin-defined keywords.
- Reuse existing WorkflowExecutor/BrowserManager/Reporter.

## Non-Goals
- No compatibility with existing YAML workflow DSL.
- No auto-generation of flows from acceptance criteria.
- No business-specific domain modeling in core.

## Architecture Overview

Business DSL
  -> Parser (DSL -> AST)
  -> Compiler (AST -> Workflow/Phase/Action)
  -> WorkflowExecutor + BrowserManager
  -> Reporter + Issue Generator

Plugin keywords
  -> Keyword Registry
  -> Plugin Manager

Locator packs
  -> Locator Registry
  -> Hybrid/Hierarchy Locators

## Components
1) DSL Parser
- Input: text DSL file
- Output: AST with source references (file, line, column)
- Validation: syntax, unknown blocks, missing tokens

2) Keyword Registry
- Core keywords: open/click/fill/wait/assert
- Plugin keywords: plugin.<name>.*
- Each keyword has a spec: params, types, default values, returns

3) Compiler
- Maps AST steps into Workflow/Phase/Action
- Resolves keyword params, variable interpolation, and locator keys
- Emits Action metadata with source_ref for error mapping
- Inserts plugin_action for plugin keywords

4) Plugin Manager
- Loads domain plugins and registers keywords
- Executes plugin actions with ScenarioContext
- Supports health checks and dependency ordering

5) Locator Packs
- All selectors live in locator packs (versioned)
- DSL uses locator keys only, never raw selectors
- Packs can be swapped per project/environment

6) Execution + Reporting
- Uses existing WorkflowExecutor, BrowserManager, Reporter
- Error mapping from Action -> DSL source_ref
- Evidence collection (screenshots/MCP) unchanged

## Keyword DSL Sketch

Example (line-oriented):

CASE "NH-SCRIPT-001"
  TAGS ["naohai", "script"]
  USE_LOCATORS "naohai-v1"

  VAR prompt = "{{script_text}}"

  STEP open url="${BASE_URL}"
  STEP click target="nav.ai_create"
  STEP fill target="editor.prompt" text="$prompt"
  STEP plugin.aigc.generate mode="storyboard"

  ASSERT text_contains target="toast" text="success"
END

Rules:
- Only keyword lines: STEP/ASSERT/VAR/TAGS/USE_LOCATORS
- No selectors, no timeouts, no sleeps in DSL
- Variables use $var or {{var}} interpolation
- Conditionals are minimal and explicit (optional extension)

## Keyword to Action Mapping
- open -> open_page action
- click -> click action with locator key
- fill -> input action with locator key
- wait -> wait_for action with policy from config
- assert.* -> assert_* actions
- plugin.* -> plugin_action (exec via Plugin Manager)

## Error Handling
- Compile-time errors: unknown keyword, missing params, invalid types
- Runtime errors: map back to DSL line via source_ref
- Plugin errors wrap into PluginError with domain/context
- Optional fallback strategies per keyword (retry/skip/degrade)

## Testing and Gates
- Parser unit tests: syntax, AST shape, source mapping
- Compiler unit tests: keyword -> action mapping snapshots
- Keyword contract tests: required params and output shape
- Plugin smoke tests: health check and minimal scenario
- CI gate: DSL purity check (no selector/timeouts)

## Open Questions
- DSL conditional blocks (if/else) scope and limits
- Keyword versioning and deprecation policy
- Locator pack selection strategy per environment
