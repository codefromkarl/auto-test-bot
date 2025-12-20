from __future__ import annotations

from abc import ABC, abstractmethod
import copy
from typing import Any, Dict, List, Optional


class TaskObserver(ABC):
    @abstractmethod
    async def get_status(
        self,
        *,
        task_id: str,
        task_type: str,
        task_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError


class SequenceTaskObserver(TaskObserver):
    """
    用于测试/模拟：按序返回状态，耗尽后重复最后一个状态。
    """

    def __init__(self, statuses: List[Dict[str, Any]]):
        if not statuses:
            raise ValueError("statuses 不能为空")
        self._statuses = [copy.deepcopy(s) for s in statuses]
        self._index = 0

    async def get_status(
        self,
        *,
        task_id: str,
        task_type: str,
        task_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self._index < len(self._statuses):
            status = self._statuses[self._index]
            self._index += 1
        else:
            status = self._statuses[-1]
        return copy.deepcopy(status)

