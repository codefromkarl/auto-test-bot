from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SourceRef:
    path: str
    line: int
    column: int = 1


@dataclass
class DslStatement:
    kind: str  # "step" or "assert"
    keyword: str
    params: Dict[str, str]
    source: SourceRef


@dataclass
class DslCase:
    name: str
    source: SourceRef
    tags: List[str] = field(default_factory=list)
    locator_pack: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    statements: List[DslStatement] = field(default_factory=list)


@dataclass
class DslFile:
    cases: List[DslCase]
    source_path: str
