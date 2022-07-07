# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param("e37510b9-3166-4f80-a919-dfaac9b696c7", id="Entity"),
        pytest.param("8bcb11e6-443b-4b92-bec2-ff1d87a224e7", id="Activity"),
        pytest.param(
            "344a405e-c7e5-4367-8a9a-41d3d9a27f81", id="SystemComponent"
        ),
        pytest.param(
            "a5642060-c9cc-4d49-af09-defaa3024bae", id="SystemFunction"
        ),
        pytest.param(
            "f632888e-51bc-4c9f-8e81-73e9404de784", id="LogicalComponent"
        ),
        pytest.param(
            "7f138bae-4949-40a1-9a88-15941f827f8c", id="LogicalFunction"
        ),
    ],
)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram

    assert diag.nodes
