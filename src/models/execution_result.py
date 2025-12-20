"""Execution result models for workflow engine"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionResult:
    """
    Standard execution result structure for workflow engine
    Ensures all required fields are present for testing and reporting
    """
    # Basic workflow info
    workflow_name: str
    overall_success: bool

    # Execution tracking
    execution_history: List[Dict[str, Any]]
    error_history: List[Dict[str, Any]]
    phase_results: List[Dict[str, Any]]

    # Context and observations
    final_context: Dict[str, Any]
    mcp_observations: List[Dict[str, Any]]

    # Timing info
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None

    # Report data
    report: Optional[Dict[str, Any]] = None

    @classmethod
    def create(cls, workflow_name: str) -> 'ExecutionResult':
        """Create a new execution result with initialized fields"""
        return cls(
            workflow_name=workflow_name,
            overall_success=True,  # Assume success until proven otherwise
            execution_history=[],
            error_history=[],
            phase_results=[],
            final_context={},
            mcp_observations=[],
            start_time=datetime.now().isoformat()
        )

    def add_execution_record(self, phase: str, step: str, action: str, status: str = "success") -> None:
        """Add a step execution record"""
        self.execution_history.append({
            "phase": phase,
            "step": step,
            "action": action,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

    def add_error_record(self, phase: str, step: str, error: Dict[str, Any]) -> None:
        """Add an error record and mark overall failure"""
        self.error_history.append({
            "phase": phase,
            "step": step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.overall_success = False

    def add_phase_result(self, phase: str, steps_executed: List[str]) -> None:
        """Add a phase execution result"""
        self.phase_results.append({
            "phase": phase,
            "steps_executed": steps_executed
        })

    def finalize(self, final_context: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the execution result and convert to dict format"""
        self.end_time = datetime.now().isoformat()
        self.final_context = final_context

        if self.start_time and self.end_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.duration_seconds = (end - start).total_seconds()

        # Convert to dict for compatibility with existing code
        return {
            "workflow_name": self.workflow_name,
            "overall_success": self.overall_success,
            "execution_history": self.execution_history,
            "error_history": self.error_history,
            "phase_results": self.phase_results,
            "final_context": self.final_context,
            "mcp_observations": self.mcp_observations,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "report": self.report or {}
        }