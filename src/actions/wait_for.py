"""WaitFor action implementation"""

from typing import Dict, Any, List, Union
from models.action import Action
from models.context import Context


class WaitForAction(Action):
    """
    Atomic action for waiting for conditions.
    Performs only waiting without business logic.
    """

    def get_step_name(self) -> str:
        return "wait_for"

    def execute(self, context: Context) -> Context:
        """
        Wait for specified condition to be met

        Args:
            context: Current execution context

        Returns:
            Updated context
        """
        condition = self.params.get('condition')
        if not condition:
            context.set_error({
                'error': "Condition parameter is required",
                'params': self.params
            }, "TEST_CONFIG_ERROR")
            return context

        try:
            timeout = self.params.get('timeout', 10000)
            interval = self.params.get('interval', 500)

            # Validate condition
            if not self._is_valid_condition(condition):
                context.set_error({
                    'error': f"Invalid condition format: {condition}",
                    'condition': condition
                }, "TEST_CONFIG_ERROR")
                return context

            # The actual waiting will be handled by browser manager
            # Here we just validate the action
            return context

        except Exception as e:
            context.set_error({
                'error': f"Failed to wait for condition: {str(e)}",
                'condition': condition
            }, "SYSTEM_FUNCTIONAL_ERROR")
            return context

    def validate(self) -> List[str]:
        """
        Validate action parameters

        Returns:
            List of validation errors
        """
        errors = []

        if 'condition' not in self.params:
            errors.append("WaitForAction requires 'condition' parameter")
        elif not self.params['condition']:
            errors.append("Condition parameter cannot be empty")

        # Validate timeout if provided
        if 'timeout' in self.params:
            timeout = self.params['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("Timeout must be a positive number")

        # Validate interval if provided
        if 'interval' in self.params:
            interval = self.params['interval']
            if not isinstance(interval, (int, float)) or interval <= 0:
                errors.append("Interval must be a positive number")

        return errors

    def _is_valid_condition(self, condition: Dict[str, Any]) -> bool:
        """
        Validate condition structure

        Args:
            condition: Condition specification

        Returns:
            True if condition appears valid
        """
        if not isinstance(condition, dict):
            return False

        # Supported condition types
        valid_condition_keys = ['selector', 'text', 'visible', 'not_visible', 'timeout']
        for key in condition.keys():
            if key not in valid_condition_keys:
                return False

        # At least one selector-based condition is required
        has_selector = 'selector' in condition
        has_text = 'text' in condition
        has_visible = 'visible' in condition
        has_not_visible = 'not_visible' in condition

        return has_selector or has_text or has_visible or has_not_visible

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': 'wait_for',
            'params': {
                'condition': self.params.get('condition', {}),
                'timeout': self.params.get('timeout', 10000),
                'interval': self.params.get('interval', 500)
            }
        }