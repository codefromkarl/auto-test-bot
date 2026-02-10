"""Framework atomic actions - generic browser interactions"""

from src.models.action import Action
from src.models.context import Context

# Atomic action classes
from src.framework.actions.click import ClickAction
from src.framework.actions.input import InputAction
from src.framework.actions.open_page import OpenPageAction
from src.framework.actions.wait_for import WaitForAction

__all__ = [
    'Action',
    'Context',
    'ClickAction',
    'InputAction',
    'OpenPageAction',
    'WaitForAction',
]
