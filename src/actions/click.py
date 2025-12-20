"""Click action implementation"""

from typing import Dict, Any, List
from models.action import Action
from models.context import Context


class ClickAction(Action):
    """
    Atomic action for clicking elements on page.
    Performs only click without business logic.
    """

    def get_step_name(self) -> str:
        return "click"

    def execute(self, context: Context) -> Context:
        """
        Locate and click element with specified selector

        Args:
            context: Current execution context

        Returns:
            Updated context
        """
        selector = self.params.get('selector')
        if not selector:
            context.set_error({
                'error': "Selector parameter is required",
                'params': self.params
            }, "TEST_CONFIG_ERROR")
            return context

        try:
            # The actual clicking will be handled by browser manager
            # Here we just validate the action
            timeout = self.params.get('timeout', 10000)

            # Validate selector format
            if not self._is_valid_selector(selector):
                context.set_error({
                    'error': f"Invalid selector format: {selector}",
                    'selector': selector
                }, "TEST_CONFIG_ERROR")
                return context

            # Success - context remains unchanged for click action
            return context

        except Exception as e:
            context.set_error({
                'error': f"Failed to click element: {str(e)}",
                'selector': selector
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
            errors.append("ClickAction requires 'selector' parameter")
        elif not self.params['selector']:
            errors.append("Selector parameter cannot be empty")

        # Validate timeout if provided
        if 'timeout' in self.params:
            timeout = self.params['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("Timeout must be a positive number")

        return errors

    def _is_valid_selector(self, selector: str) -> bool:
        """
        Basic selector validation

        Args:
            selector: CSS selector to validate

        Returns:
            True if selector appears valid
        """
        # Basic validation for common CSS selectors
        if not selector or len(selector.strip()) == 0:
            return False

        # Check for common valid patterns
        valid_patterns = [
            '#',           # ID selector
            '.',           # Class selector
            '[',           # Attribute selector
            '>',            # Child combinator
            '+',            # Adjacent sibling
            '~',            # General sibling
        ]

        # Allow tag names (simple case)
        if ' ' not in selector and not any(p in selector for p in valid_patterns):
            return selector.isidentifier()

        # More complex validation would go here in production
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': 'click',
            'params': {
                'selector': self.params.get('selector', ''),
                'timeout': self.params.get('timeout', 10000)
            }
        }