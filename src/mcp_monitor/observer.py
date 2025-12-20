"""MCP Observer for evidence collection"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class MCPObserver(ABC):
    """
    Abstract base for MCP observation.
    Serves as observer and evidence collector, not flow controller.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP observer

        Args:
            config: System configuration
        """
        self.config = config.get('mcp', {})
        self.logger = logging.getLogger(__name__)
        self._is_observing = False

    async def start_observation(self) -> None:
        """Start MCP observation for all monitors"""
        self._is_observing = True
        self.logger.info("MCP observation started")

    async def stop_observation(self) -> Dict[str, Any]:
        """
        Stop MCP observation and collect evidence

        Returns:
            Collected evidence from all monitors
        """
        self._is_observing = False
        self.logger.info("MCP observation stopped")

        # Collect evidence from all monitors
        evidence = {}

        try:
            # Implementation will add concrete monitor collection
            console_evidence = await self._collect_console_evidence()
            if console_evidence:
                evidence['console'] = console_evidence

            network_evidence = await self._collect_network_evidence()
            if network_evidence:
                evidence['network'] = network_evidence

            performance_evidence = await self._collect_performance_evidence()
            if performance_evidence:
                evidence['performance'] = performance_evidence

            dom_evidence = await self._collect_dom_evidence()
            if dom_evidence:
                evidence['dom'] = dom_evidence

            return evidence

        except Exception as e:
            self.logger.error(f"Error collecting MCP evidence: {str(e)}")
            return {}

    @abstractmethod
    async def _collect_console_evidence(self) -> Optional[Dict[str, Any]]:
        """Collect console log evidence"""
        pass

    @abstractmethod
    async def _collect_network_evidence(self) -> Optional[Dict[str, Any]]:
        """Collect network request/response evidence"""
        pass

    @abstractmethod
    async def _collect_performance_evidence(self) -> Optional[Dict[str, Any]]:
        """Collect performance trace evidence"""
        pass

    @abstractmethod
    async def _collect_dom_evidence(self) -> Optional[Dict[str, Any]]:
        """Collect DOM snapshot evidence"""
        pass

    def is_observing(self) -> bool:
        """Check if observation is active"""
        return self._is_observing