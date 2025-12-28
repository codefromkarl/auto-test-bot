from typing import Dict

from models import Workflow
from models.phase import Phase
from models.action import Action

from .ast import DslCase
from .registry import KeywordRegistry
from .locator_packs import LocatorPackRegistry


def compile_case(case: DslCase, registry: KeywordRegistry, packs: LocatorPackRegistry) -> Workflow:
    workflow = Workflow(name=case.name)
    phase = Phase(name="main")

    for stmt in case.statements:
        spec = registry.get(stmt.keyword)
        spec.validate(stmt.params)

        if spec.is_plugin:
            if not spec.plugin_name:
                raise ValueError("plugin_name is required for plugin keyword")
            params = {"plugin": spec.plugin_name, "keyword": spec.name, **stmt.params}
            action = Action.create("plugin_action", params)
        else:
            params = dict(stmt.params)
            if "target" in params:
                if not case.locator_pack:
                    raise ValueError("locator_pack is required when using target")
                params["selector"] = packs.resolve(case.locator_pack, params.pop("target"))

            action = Action.create(spec.action, params)
        phase.add_step(action)

    workflow.add_phase(phase)
    return workflow
