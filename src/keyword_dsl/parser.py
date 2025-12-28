import json
import re
import shlex
from typing import List

from .ast import DslFile, DslCase, DslStatement, SourceRef


class DslParseError(ValueError):
    pass


_CASE_RE = re.compile(r'^CASE\s+"(?P<name>.+)"\s*$')
_TAGS_RE = re.compile(r'^TAGS\s+(?P<json>\[.*\])\s*$')
_LOCATORS_RE = re.compile(r'^USE_LOCATORS\s+"(?P<name>.+)"\s*$')
_VAR_RE = re.compile(r'^VAR\s+(?P<name>\w+)\s*=\s*"(?P<value>.*)"\s*$')


def parse_dsl(text: str, source_path: str = "<memory>") -> DslFile:
    cases: List[DslCase] = []
    current: DslCase | None = None

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line == "END":
            if not current:
                raise DslParseError(f"END without CASE at {source_path}:{idx}")
            cases.append(current)
            current = None
            continue

        m = _CASE_RE.match(line)
        if m:
            if current:
                raise DslParseError(f"Nested CASE at {source_path}:{idx}")
            current = DslCase(name=m.group("name"), source=SourceRef(source_path, idx))
            continue

        if not current:
            raise DslParseError(f"Line outside CASE at {source_path}:{idx}")

        m = _TAGS_RE.match(line)
        if m:
            current.tags = json.loads(m.group("json"))
            continue

        m = _LOCATORS_RE.match(line)
        if m:
            current.locator_pack = m.group("name")
            continue

        m = _VAR_RE.match(line)
        if m:
            current.variables[m.group("name")] = m.group("value")
            continue

        tokens = shlex.split(line)
        if not tokens:
            continue
        head = tokens[0]
        if head in {"STEP", "ASSERT"}:
            if len(tokens) < 2:
                raise DslParseError(f"Missing keyword at {source_path}:{idx}")
            keyword = tokens[1]
            params = {}
            for token in tokens[2:]:
                if "=" not in token:
                    raise DslParseError(f"Invalid param '{token}' at {source_path}:{idx}")
                key, value = token.split("=", 1)
                params[key] = value
            current.statements.append(
                DslStatement(
                    kind="step" if head == "STEP" else "assert",
                    keyword=keyword,
                    params=params,
                    source=SourceRef(source_path, idx),
                )
            )
            continue

        raise DslParseError(f"Unknown line '{line}' at {source_path}:{idx}")

    if current:
        raise DslParseError(f"Missing END for CASE {current.name} at {source_path}")

    return DslFile(cases=cases, source_path=source_path)
