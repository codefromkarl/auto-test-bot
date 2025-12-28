"""Action model for minimal interaction units"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .context import Context


class Action(ABC):
    """
    Abstract base class for atomic actions.
    Actions only perform minimal interactions without business logic.
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize an action

        Args:
            params: Action-specific parameters
        """
        self.params = params or {}
        # Set action type based on class name
        self.action = self.__class__.__name__.lower().replace('action', '')

    @abstractmethod
    def execute(self, context: Context) -> Context:
        """
        Execute the action

        Args:
            context: Current execution context

        Returns:
            Updated context
        """
        pass

    @abstractmethod
    def get_step_name(self) -> str:
        """
        Get step name for tracking

        Returns:
            Step name identifier
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert action to dictionary

        Returns:
            Dictionary representation
        """
        return {
            'type': self.__class__.__name__,
            'params': self.params
        }

    def validate(self) -> List[str]:
        """
        Validate action parameters

        Returns:
            List of validation errors
        """
        return []

    @classmethod
    def create(cls, action_type: str, params: Dict[str, Any]) -> 'Action':
        """
        Factory method to create action instances

        Args:
            action_type: Type of action to create
            params: Action parameters

        Returns:
            Action instance
        """
        action_classes = {
            'open_page': OpenPageAction,
            'click': ClickAction,
            'input': InputAction,
            'wait_for': WaitForAction,
            'screenshot': ScreenshotAction,
            'clear_input': ClearInputAction,
            'extract_video_info': ExtractVideoInfoAction,
            'assert_logged_in': AssertLoggedInAction,
            'upload_file': UploadFileAction,
            'assert_element_exists': AssertElementExistsAction,
            'assert_element_count': AssertElementCountAction,
            'assert_element_selected': AssertElementSelectedAction,
            'assert_element_not_selected': AssertElementNotSelectedAction,
            'assert_element_value_contains': AssertElementValueContainsAction,
            'move_slider': MoveSliderAction,
            'save_data': SaveDataAction,
            'plugin_action': PluginAction,
        }

        # Check if this is a semantic action (prefixed with 'rf_')
        if action_type.startswith('rf_'):
            from .semantic_action import SemanticAction
            semantic_type = action_type[3:]  # Remove 'rf_' prefix
            return SemanticAction.create_semantic(semantic_type, params)

        if action_type not in action_classes:
            raise ValueError(f"Unknown action type: {action_type}")

        return action_classes[action_type](params)


class OpenPageAction(Action):
    """Action for navigating to a URL"""

    def get_step_name(self) -> str:
        return "open_page"

    def execute(self, context: Context) -> Context:
        # Implementation will be in actions package
        context.current_url = self.params.get('url', '')
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'url' not in self.params:
            errors.append("OpenPageAction requires 'url' parameter")
        return errors


class ClickAction(Action):
    """Action for clicking elements"""

    def get_step_name(self) -> str:
        return "click"

    def execute(self, context: Context) -> Context:
        # Implementation will be in actions package
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("ClickAction requires 'selector' parameter")
        return errors


class InputAction(Action):
    """Action for inputting text"""

    def get_step_name(self) -> str:
        return "input"

    def execute(self, context: Context) -> Context:
        # Implementation will be in actions package
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("InputAction requires 'selector' parameter")
        if 'text' not in self.params:
            errors.append("InputAction requires 'text' parameter")
        return errors


class WaitForAction(Action):
    """Action for waiting for conditions"""

    def get_step_name(self) -> str:
        return "wait_for"

    def execute(self, context: Context) -> Context:
        # Implementation will be in actions package
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'condition' not in self.params:
            errors.append("WaitForAction requires 'condition' parameter")
        return errors


class ScreenshotAction(Action):
    """Action for taking a screenshot"""

    def get_step_name(self) -> str:
        return "screenshot"

    def execute(self, context: Context) -> Context:
        # Actual screenshot handled by workflow executor/browser manager
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'save_path' not in self.params and 'path' not in self.params:
            errors.append("ScreenshotAction requires 'save_path' (or 'path') parameter")
        return errors


class ClearInputAction(Action):
    """Action for clearing an input"""

    def get_step_name(self) -> str:
        return "clear_input"

    def execute(self, context: Context) -> Context:
        # Actual clear handled by workflow executor/browser manager
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("ClearInputAction requires 'selector' parameter")
        return errors


class ExtractVideoInfoAction(Action):
    """Action for extracting video element info"""

    def get_step_name(self) -> str:
        return "extract_video_info"

    def execute(self, context: Context) -> Context:
        # Actual extraction handled by workflow executor/browser manager
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("ExtractVideoInfoAction requires 'selector' parameter")
        return errors


class AssertLoggedInAction(Action):
    """Action for asserting login status based on sessionStorage token/user_info"""

    def get_step_name(self) -> str:
        return "assert_logged_in"

    def execute(self, context: Context) -> Context:
        # Actual assertion handled by workflow executor/browser manager
        return context


class UploadFileAction(Action):
    """Action for uploading a file via <input type=file>"""

    def get_step_name(self) -> str:
        return "upload_file"

    def execute(self, context: Context) -> Context:
        # Actual upload handled by workflow executor/browser manager
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("UploadFileAction requires 'selector' parameter")
        if 'file_path' not in self.params and 'path' not in self.params:
            errors.append("UploadFileAction requires 'file_path' (or 'path') parameter")
        return errors


class AssertElementExistsAction(Action):
    """Action for asserting an element exists (optionally visible)"""

    def get_step_name(self) -> str:
        return "assert_element_exists"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("AssertElementExistsAction requires 'selector' parameter")
        return errors


class AssertElementCountAction(Action):
    """Action for asserting element count (exact or range)"""

    def get_step_name(self) -> str:
        return "assert_element_count"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("AssertElementCountAction requires 'selector' parameter")
        if not any(k in self.params for k in ('expected_count', 'min_count', 'max_count')):
            errors.append("AssertElementCountAction requires one of 'expected_count', 'min_count', or 'max_count'")
        return errors


class AssertElementSelectedAction(Action):
    """Action for asserting an element is selected/active"""

    def get_step_name(self) -> str:
        return "assert_element_selected"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("AssertElementSelectedAction requires 'selector' parameter")
        return errors


class AssertElementNotSelectedAction(Action):
    """Action for asserting an element is not selected/active"""

    def get_step_name(self) -> str:
        return "assert_element_not_selected"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("AssertElementNotSelectedAction requires 'selector' parameter")
        return errors


class AssertElementValueContainsAction(Action):
    """Action for asserting input/textarea value contains expected substring"""

    def get_step_name(self) -> str:
        return "assert_element_value_contains"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("AssertElementValueContainsAction requires 'selector' parameter")
        if 'expected' not in self.params:
            errors.append("AssertElementValueContainsAction requires 'expected' parameter")
        return errors


class MoveSliderAction(Action):
    """Action for setting <input type=range> value"""

    def get_step_name(self) -> str:
        return "move_slider"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'selector' not in self.params:
            errors.append("MoveSliderAction requires 'selector' parameter")
        if 'value' not in self.params:
            errors.append("MoveSliderAction requires 'value' parameter")
        return errors


class PluginAction(Action):
    """Action for plugin execution (handled by executor)."""

    def get_step_name(self) -> str:
        return "plugin_action"

    def execute(self, context: Context) -> Context:
        return context


class SaveDataAction(Action):
    """Action for saving arbitrary data into execution context"""

    def get_step_name(self) -> str:
        return "save_data"

    def execute(self, context: Context) -> Context:
        return context

    def validate(self) -> List[str]:
        errors = []
        if 'key' not in self.params:
            errors.append("SaveDataAction requires 'key' parameter")
        if 'value' not in self.params:
            errors.append("SaveDataAction requires 'value' parameter")
        return errors
