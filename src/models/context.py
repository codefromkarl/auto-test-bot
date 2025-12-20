"""Context model for state management"""

from typing import Dict, Any, Optional
from threading import Lock
import copy


class Context:
    """
    Context serves as a state carrier, not a logger.
    Contains all required fields for execution tracking.
    """

    def __init__(self):
        """Initialize context with required fields"""
        # Required fields per specification
        self.workflow_name: Optional[str] = None
        self.current_phase: Optional[str] = None
        self.current_step: Optional[str] = None
        self.current_url: Optional[str] = None
        self.last_error: Optional[Dict[str, Any]] = None

        # Additional state for execution
        self._state: Dict[str, Any] = {}
        self._history: list = []
        self._lock = Lock()

    # Property access with thread safety
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value with thread safety"""
        with self._lock:
            return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set state value with thread safety"""
        with self._lock:
            self._state[key] = value
            self._save_snapshot(f"set {key}={value}")

    def update_url(self, url: str) -> None:
        """Update current URL atomically"""
        with self._lock:
            self.current_url = url
            self._save_snapshot(f"url={url}")

    def update_phase(self, phase: str) -> None:
        """Update current phase atomically"""
        with self._lock:
            self.current_phase = phase
            self._save_snapshot(f"phase={phase}")

    def update_step(self, step: str) -> None:
        """Update current step atomically"""
        with self._lock:
            self.current_step = step
            self._save_snapshot(f"step={step}")

    def set_error(self, error: Dict[str, Any], error_type: str = "SYSTEM_FUNCTIONAL_ERROR") -> None:
        """Set error state atomically"""
        with self._lock:
            self.last_error = {
                **error,
                'type': error_type,
                'timestamp': self._get_timestamp()
            }
            self._save_snapshot(f"error={error}")

    def clear_error(self) -> None:
        """Clear error state atomically"""
        with self._lock:
            self.last_error = None
            self._save_snapshot("error_cleared")

    def create_snapshot(self) -> Dict[str, Any]:
        """Create current state snapshot"""
        with self._lock:
            snapshot = {
                'workflow_name': self.workflow_name,
                'current_phase': self.current_phase,
                'current_step': self.current_step,
                'current_url': self.current_url,
                'last_error': copy.deepcopy(self.last_error),
                'state': copy.deepcopy(self._state),
                'data': copy.deepcopy(self._state),  # Add data field for compatibility
                'timestamp': self._get_timestamp()
            }
            # Flatten state to top-level for compatibility with callers that expect direct fields.
            for key, value in copy.deepcopy(self._state).items():
                snapshot.setdefault(key, value)
            return snapshot

    def restore_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot"""
        with self._lock:
            self.workflow_name = snapshot.get('workflow_name')
            self.current_phase = snapshot.get('current_phase')
            self.current_step = snapshot.get('current_step')
            self.current_url = snapshot.get('current_url')
            self.last_error = snapshot.get('last_error')
            self._state = copy.deepcopy(snapshot.get('data', {}))

    def is_error_state(self) -> bool:
        """Check if context is in error state"""
        return self.last_error is not None

    def get_error_summary(self) -> Optional[str]:
        """Get human-readable error summary"""
        if not self.last_error:
            return None
        error_type = self.last_error.get('type', 'UNKNOWN')
        error_desc = self.last_error.get('error', 'Unknown error')
        step = self.last_error.get('step', 'Unknown step')
        phase = self.last_error.get('phase', 'Unknown phase')
        return f"{error_type}: Error in phase '{phase}', step '{step}': {error_desc}"

    def _save_snapshot(self, change_desc: str) -> None:
        """Save state change to history"""
        # Create snapshot without acquiring lock to avoid deadlock
        # since this is called from within already locked context
        snapshot = {
            'workflow_name': self.workflow_name,
            'current_phase': self.current_phase,
            'current_step': self.current_step,
            'current_url': self.current_url,
            'last_error': copy.deepcopy(self.last_error) if self.last_error else None,
            'state': copy.deepcopy(self._state),
            'data': copy.deepcopy(self._state),  # Add data field for compatibility
            'timestamp': self._get_timestamp(),
            'change': change_desc
        }
        self._history.append(snapshot)

        # Keep only last 100 snapshots to prevent memory issues
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_history(self, limit: int = 10) -> list:
        """Get recent state history"""
        with self._lock:
            return self._history[-limit:]

    # Data storage methods for test compatibility
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from state storage"""
        return self.get_state(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """Set data in state storage"""
        self.set_state(key, value)
