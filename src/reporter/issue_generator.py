import os
import time
import json
from typing import Dict, Any, Optional

class IssueGenerator:
    """
    Generates structured Issue files in .ai/issues/ when a workflow fails.
    """
    
    def __init__(self, issues_dir: str = ".ai/issues"):
        self.issues_dir = issues_dir
        os.makedirs(self.issues_dir, exist_ok=True)

    def generate_issue(self, workflow_name: str, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Creates a new Issue markdown file based on the execution result.
        
        Args:
            workflow_name: Name of the workflow
            result: Execution result dictionary
            config: Test configuration
            
        Returns:
            Path to the created issue file
        """
        if result.get('overall_success', True):
            return ""

        timestamp = int(time.time())
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        
        # Determine Issue ID (simple increment for now, or timestamp based)
        issue_id = f"AUTO-{timestamp}"
        filename = f"ISSUE-{issue_id}.md"
        filepath = os.path.join(self.issues_dir, filename)

        error_info = self._extract_root_cause(result)
        
        # Prepare context for template
        selector_info = error_info.get('params', {}).get('selector', 'N/A')
        
        content = f"""# Issue #{issue_id}: [Auto-Bug] Workflow '{workflow_name}' Failed

- **Status**: OPEN
- **Priority**: High
- **Created**: {date_str}
- **Workflow**: `{workflow_name}`
- **Type**: Automated Test Failure

## Description

### ❗ Symptom
Workflow execution failed during phase **{error_info['phase']}**, step **{error_info['step']}**.

**Error Message:**
```
{error_info['message']}
```

### 🔍 Context
- **Phase**: `{error_info['phase']}`
- **Step**: `{error_info['step']}`
- **Action**: `{error_info['action']}`
- **Params**: 
```json
{json.dumps(error_info['params'], indent=2, ensure_ascii=False)}
```

### 📸 Evidence
"""
        
        # Add Screenshots
        if error_info.get('screenshot'):
            content += f"\n![Failure Screenshot](../../{error_info['screenshot']})\n"
            content += f"\n*Path: `{error_info['screenshot']}`*\n"

        content += """
### 📄 Recent Logs
<details>
<summary>Click to expand execution history</summary>

```json
"""
        # Add last few steps of history
        history = result.get('execution_history', [])
        recent_history = history[-5:] if len(history) > 5 else history
        content += json.dumps(recent_history, indent=2, ensure_ascii=False)
        
        content += f"""
```
</details>

## Diagnosis & Recovery
- **Potential Cause**: The automation script expected a specific state or element that was not found. This could be due to a UI change, network latency, or an unhandled application state (e.g., empty state).
- **Suggested Fix**:
    1. Check if the selector `{selector_info}` is correct.
    2. Verify if the page requires intermediate steps (like handling a wizard or empty state).
    3. Run with `--debug` to see more details.

## Repro Command
```bash
python3 src/main_workflow.py --workflow workflows/at/{workflow_name}.yaml
```
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return filepath

    def _extract_root_cause(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts the first critical error from the result."""
        default_error = {
            "phase": "unknown",
            "step": "unknown",
            "action": "unknown",
            "message": "Unknown error occurred",
            "params": {},
            "screenshot": None
        }

        # Check error_history first
        if result.get('error_history'):
            first_error = result['error_history'][-1] # Usually the last one is the fatal one
            default_error.update({
                "phase": first_error.get('phase', 'unknown'),
                "step": first_error.get('step', 'unknown'),
                "message": first_error.get('error', 'Unknown error')
            })

        # Try to find matching detailed execution record
        history = result.get('execution_history', [])
        for record in reversed(history):
            if record.get('status') == 'failed':
                default_error['action'] = record.get('action', default_error['step'])
                default_error['params'] = record.get('params', {})
                break
                
        # Look for screenshot in context or params
        # This is best-effort; might need to check file system for recent screenshots
        return default_error