"""Phase model representing mental model stages"""

from typing import List, Dict, Any, Optional
from .action import Action
from .context import Context


class Phase:
    """
    Phase represents a mental model stage containing ordered actions.
    Each phase corresponds to a user's mental stage.
    """

    def __init__(self, name: str, steps: List[Action] = None):
        """
        Initialize a phase

        Args:
            name: Phase name representing mental model stage
            steps: Ordered list of actions in this phase
        """
        self.name = name
        self.steps = steps or []
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: Action) -> 'Phase':
        """
        Add an action step to the phase

        Args:
            step: Action to add

        Returns:
            Self for chaining
        """
        self.steps.append(step)
        return self

    def execute(self, context: Context) -> Context:
        """
        Execute all steps in the phase

        Args:
            context: Execution context

        Returns:
            Updated context after execution
        """
        context.current_phase = self.name

        for step_index, step in enumerate(self.steps):
            context.current_step = step.get_step_name()

            try:
                context = step.execute(context)

                # Check for errors after each step
                if context.last_error:
                    context.last_error['step'] = step.get_step_name()
                    break

            except Exception as e:
                context.last_error = {
                    'step': step.get_step_name(),
                    'phase': self.name,
                    'error': str(e),
                    'type': 'SYSTEM_FUNCTIONAL_ERROR'
                }
                break

        return context

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Phase':
        """
        Create phase from dictionary data

        Args:
            data: Dictionary containing phase data

        Returns:
            Phase instance
        """
        name = data.get('name', 'unnamed_phase')
        phase = cls(name)

        # Parse steps
        if 'steps' in data:
            for step_data in data['steps']:
                # DSL v1: - open_page: { url: "..." }
                if isinstance(step_data, dict) and 'action' not in step_data:
                    for step_name, step_params in step_data.items():
                        action = Action.create(step_name, step_params or {})
                        phase.add_step(action)
                    continue

                # DSL v2 (action-style): - action: "open_page" / other keys are params
                if isinstance(step_data, dict) and 'action' in step_data:
                    step_name = step_data.get('action')
                    step_params = {k: v for k, v in step_data.items() if k != 'action'}
                    action = Action.create(step_name, step_params)
                    phase.add_step(action)
                    continue

                raise ValueError(f"Invalid step format in phase '{name}': {step_data}")

        # Store metadata
        phase.metadata = {k: v for k, v in data.items() if k not in ['name', 'steps']}

        return phase

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert phase to dictionary

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'steps': [{step.get_step_name(): step.to_dict()} for step in self.steps],
            **self.metadata
        }

    def validate(self) -> List[str]:
        """
        Validate phase structure

        Returns:
            List of validation errors
        """
        errors = []

        if not self.name:
            errors.append("Phase name is required")

        if not self.steps:
            errors.append("Phase must have at least one step")

        # Validate each step
        for step in self.steps:
            step_errors = step.validate()
            errors.extend([f"Step '{step.get_step_name()}': {err}" for err in step_errors])

        return errors
