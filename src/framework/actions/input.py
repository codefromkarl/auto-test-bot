"""Input action implementation"""

from typing import Dict, Any, List
from src.models.action import Action
from src.models.context import Context


class InputAction(Action):
    """
    Atomic action for inputting text into form fields.
    Performs only text input without business logic.
    """

    def get_step_name(self) -> str:
        return "input"

    def execute(self, context: Context) -> Context:
        """
        Input text into specified element

        Args:
            context: Current execution context

        Returns:
            Updated context
        """
        selector = self.params.get('selector')
        text = self.params.get('text')

        if not selector:
            context.set_error({
                'error': "Selector parameter is required",
                'params': self.params
            }, "TEST_CONFIG_ERROR")
            return context

        if text is None:
            context.set_error({
                'error': "Text parameter is required",
                'params': self.params
            }, "TEST_CONFIG_ERROR")
            return context

        try:
            # Validate selector
            if not self._is_valid_selector(selector):
                context.set_error({
                    'error': f"Invalid selector format: {selector}",
                    'selector': selector
                }, "TEST_CONFIG_ERROR")
                return context

            # The actual input will be handled by browser manager
            # Here we just validate the action
            clear_first = self.params.get('clear', False)
            timeout = self.params.get('timeout', 10000)

            return context

        except Exception as e:
            context.set_error({
                'error': f"Failed to input text: {str(e)}",
                'selector': selector,
                'text': text[:100] + '...' if len(text) > 100 else text  # Truncate long text for logging
            }, "SYSTEM_FUNCTIONAL_ERROR")
            return context

    def validate(self) -> List[str]:
        """
        Validate action parameters

        Returns:
            List of validation errors
        """
        errors = []

        if 'selector' not in self.params:
            errors.append("InputAction requires 'selector' parameter")
        elif not self.params['selector']:
            errors.append("Selector parameter cannot be empty")

        if 'text' not in self.params:
            errors.append("InputAction requires 'text' parameter")

        # Validate optional parameters
        if 'timeout' in self.params:
            timeout = self.params['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("Timeout must be a positive number")

        if 'clear' in self.params:
            clear = self.params['clear']
            if not isinstance(clear, bool):
                errors.append("Clear must be a boolean")

        return errors

    def _is_valid_selector(self, selector: str) -> bool:
        """
        Basic selector validation

        Args:
            selector: CSS selector to validate

        Returns:
            True if selector appears valid
        """
        if not selector or len(selector.strip()) == 0:
            return False

        # Allow common input selectors
        valid_patterns = [
            '#',           # ID selector
            '.',           # Class selector
            '[',           # Attribute selector
            'input',        # Tag name
            'textarea',     # Tag name
        ]

        if ' ' not in selector and not any(p in selector for p in valid_patterns):
            return selector.lower() in ['input', 'textarea']

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': 'input',
            'params': {
                'selector': self.params.get('selector', ''),
                'text': self.params.get('text', ''),
                'clear': self.params.get('clear', False),
                'timeout': self.params.get('timeout', 10000)
            }
        }