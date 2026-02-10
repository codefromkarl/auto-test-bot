"""Semantic actions for RF-style intent-driven automation"""

from typing import Dict, Any, List, Type
from abc import ABC, abstractmethod
from .action import Action
from .context import Context


class SemanticAction(Action):
    """
    Base class for semantic actions that combine multiple atomic actions
    to represent business intent rather than low-level interactions.

    Semantic actions encapsulate:
    - Business logic and state management
    - Recovery and fallback mechanisms
    - Complex multi-step workflows
    """
    
    _registry: Dict[str, Type['SemanticAction']] = {}

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        # Semantic actions use a different naming convention
        self.action = self.__class__.__name__.lower().replace('semanticaction', '')

    @classmethod
    def register(cls, name: str, action_class: Type['SemanticAction']) -> None:
        """
        Register a semantic action class.
        
        Args:
            name: The action type name (e.g., 'enter_ai_creation')
            action_class: The class implementing the action
        """
        cls._registry[name] = action_class

    @abstractmethod
    def get_atomic_actions(self) -> List[Action]:
        """
        Get the list of atomic actions that compose this semantic action

        Returns:
            List of atomic actions to execute
        """
        pass

    def execute(self, context: Context) -> Context:
        """
        Execute the semantic action by composing atomic actions

        Args:
            context: Current execution context

        Returns:
            Updated context
        """
        try:
            # Pre-execution setup and validation
            context = self._prepare_execution(context)

            # Execute composed atomic actions
            atomic_actions = self.get_atomic_actions()
            for atomic_action in atomic_actions:
                context = atomic_action.execute(context)
                if context.has_error():
                    # Attempt recovery if possible
                    context = self._handle_error(context, atomic_action)
                    if context.has_error():
                        break  # Recovery failed, stop execution

            # Post-execution cleanup and state updates
            context = self._finalize_execution(context)

        except Exception as e:
            context.set_error({
                'error': f"Semantic action failed: {str(e)}",
                'semantic_action': self.__class__.__name__,
                'params': self.params
            }, "SEMANTIC_ACTION_ERROR")

        return context

    def _prepare_execution(self, context: Context) -> Context:
        """
        Prepare for execution - validate inputs and set up state

        Args:
            context: Current context

        Returns:
            Updated context
        """
        # Default implementation - subclasses can override
        return context

    def _handle_error(self, context: Context, failed_action: Action) -> Context:
        """
        Handle execution errors with recovery attempts

        Args:
            context: Context with error
            failed_action: The atomic action that failed

        Returns:
            Context possibly recovered from error
        """
        # Default implementation - subclasses can override for custom recovery
        return context

    def _finalize_execution(self, context: Context) -> Context:
        """
        Finalize execution - clean up and update persistent state

        Args:
            context: Current context

        Returns:
            Final context
        """
        # Default implementation - subclasses can override
        return context

    @classmethod
    def create_semantic(cls, action_type: str, params: Dict[str, Any]) -> 'SemanticAction':
        """
        Factory method for semantic actions

        Args:
            action_type: Type of semantic action to create
            params: Action parameters

        Returns:
            SemanticAction instance
        """
        if action_type not in cls._registry:
            raise ValueError(f"Unknown semantic action type: {action_type}. Registered actions: {list(cls._registry.keys())}")

        return cls._registry[action_type](params)