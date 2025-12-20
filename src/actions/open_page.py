"""OpenPage action implementation"""

from typing import Dict, Any
from models.action import Action
from models.context import Context


class OpenPageAction(Action):
    """
    Atomic action for navigating to a URL.
    Performs only navigation without business logic.
    """

    def get_step_name(self) -> str:
        return "open_page"

    def execute(self, context: Context) -> Context:
        """
        Navigate to specified URL and wait for page load

        Args:
            context: Current execution context

        Returns:
            Updated context with new URL
        """
        url = self.params.get('url')
        if not url:
            context.set_error({
                'error': "URL parameter is required",
                'params': self.params
            }, "TEST_CONFIG_ERROR")
            return context

        try:
            # The actual navigation will be handled by browser manager
            # Here we just update the context state
            context.update_url(url)
            return context

        except Exception as e:
            context.set_error({
                'error': f"Failed to navigate to {url}: {str(e)}",
                'url': url
            }, "SYSTEM_FUNCTIONAL_ERROR")
            return context

    def validate(self) -> list:
        """
        Validate action parameters

        Returns:
            List of validation errors
        """
        errors = []

        if 'url' not in self.params:
            errors.append("OpenPageAction requires 'url' parameter")
        elif not self.params['url']:
            errors.append("URL parameter cannot be empty")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'type': 'open_page',
            'params': {
                'url': self.params.get('url', '')
            }
        }