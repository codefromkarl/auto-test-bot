"""Workflow model for the highest abstraction layer"""

from typing import List, Dict, Any, Optional
import yaml

from .phase import Phase
from .action import Action
from .context import Context


class Workflow:
    """
    Workflow represents the highest abstraction layer containing phases.
    Supports YAML DSL v1 format.
    """

    def __init__(
        self,
        name: str,
        phases: List[Phase] = None,
        suite_setup: List[Action] = None,
        error_recovery: List[Action] = None,
        success_criteria: List[str] = None,
    ):
        """
        Initialize a workflow

        Args:
            name: Workflow name
            phases: List of phases in execution order
        """
        self.name = name
        self.phases = phases or []
        self.suite_setup = suite_setup or []
        self.error_recovery = error_recovery or []
        self.success_criteria = success_criteria or []
        self.metadata: Dict[str, Any] = {}

    @staticmethod
    def _parse_steps_list(steps: Any, container_name: str) -> List[Action]:
        """解析 DSL v1/v2 steps 列表为 Action 列表（用于 suite_setup / error_recovery）"""
        parsed: List[Action] = []
        if not steps:
            return parsed
        if not isinstance(steps, list):
            raise ValueError(f"Invalid '{container_name}': expected list, got {type(steps).__name__}")

        for step_data in steps:
            # DSL v1: - open_page: { url: "..." }
            if isinstance(step_data, dict) and 'action' not in step_data:
                for step_name, step_params in step_data.items():
                    parsed.append(Action.create(step_name, step_params or {}))
                continue

            # DSL v2: - action: open_page / other keys are params
            if isinstance(step_data, dict) and 'action' in step_data:
                step_name = step_data.get('action')
                step_params = {k: v for k, v in step_data.items() if k != 'action'}
                parsed.append(Action.create(step_name, step_params))
                continue

            raise ValueError(f"Invalid step format in '{container_name}': {step_data}")

        return parsed

    def add_phase(self, phase: Phase) -> 'Workflow':
        """
        Add a phase to the workflow

        Args:
            phase: Phase to add

        Returns:
            Self for chaining
        """
        self.phases.append(phase)
        return self

    def execute(self, context: Context) -> Context:
        """
        Execute the workflow

        Args:
            context: Execution context

        Returns:
            Updated context after execution
        """
        context.workflow_name = self.name

        for phase_index, phase in enumerate(self.phases):
            context.current_phase = phase.name
            context = phase.execute(context)

            # Check for errors after each phase
            if context.last_error:
                context.last_error['phase'] = phase.name
                break

        return context

    def resolve_metadata(self, lookup, selectors=None) -> Dict[str, Any]:
        """Resolve semantic variables in workflow metadata."""
        from .semantic_variables import resolve_semantic_value

        resolved = resolve_semantic_value(self.metadata or {}, lookup=lookup, selectors=selectors)
        return resolved if isinstance(resolved, dict) else dict(self.metadata or {})

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'Workflow':
        """
        Parse workflow from YAML DSL v1 content

        Args:
            yaml_content: YAML string content

        Returns:
            Workflow instance
        """
        try:
            data = yaml.safe_load(yaml_content)

            if not data or 'workflow' not in data:
                raise ValueError("Invalid workflow DSL: missing 'workflow' key")

            workflow_data = data['workflow']
            name = workflow_data.get('name', 'unnamed')

            workflow = cls(name)

            # Parse suite_setup / error_recovery / success_criteria (RF extensions)
            if 'suite_setup' in workflow_data:
                workflow.suite_setup = cls._parse_steps_list(workflow_data.get('suite_setup'), 'suite_setup')
            if 'error_recovery' in workflow_data:
                workflow.error_recovery = cls._parse_steps_list(workflow_data.get('error_recovery'), 'error_recovery')
            if 'success_criteria' in workflow_data:
                criteria = workflow_data.get('success_criteria') or []
                if not isinstance(criteria, list):
                    raise ValueError("Invalid 'success_criteria': expected list of strings")
                workflow.success_criteria = [str(x) for x in criteria]

            # Parse phases
            if 'phases' in workflow_data:
                for phase_data in workflow_data['phases']:
                    phase = Phase.from_dict(phase_data)
                    workflow.add_phase(phase)

            # Store metadata
            workflow.metadata = {k: v for k, v in workflow_data.items() if k not in ['name', 'phases', 'suite_setup', 'error_recovery', 'success_criteria']}

            # Validate workflow after creation
            validation_errors = workflow.validate()
            if validation_errors:
                raise ValueError(f"Invalid workflow structure: {', '.join(validation_errors)}")

            return workflow

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing workflow: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert workflow to dictionary

        Returns:
            Dictionary representation
        """
        return {
            'workflow': {
                'name': self.name,
                **({'suite_setup': [a.to_dict() for a in self.suite_setup]} if self.suite_setup else {}),
                'phases': [phase.to_dict() for phase in self.phases],
                **({'success_criteria': list(self.success_criteria)} if self.success_criteria else {}),
                **({'error_recovery': [a.to_dict() for a in self.error_recovery]} if self.error_recovery else {}),
                **self.metadata
            }
        }

    def validate(self) -> List[str]:
        """
        Validate workflow structure

        Returns:
            List of validation errors
        """
        errors = []

        if not self.name:
            errors.append("Workflow name is required")

        if not self.phases:
            errors.append("Workflow must have at least one phase")

        return errors
