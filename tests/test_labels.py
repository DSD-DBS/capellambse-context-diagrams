# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(
            "8bcb11e6-443b-4b92-bec2-ff1d87a224e7", id="OperationalCapability"
        ),
        pytest.param(
            "230c4621-7e0a-4d0a-9db2-d4ba5e97b3df", id="SystemComponent Root"
        ),
        pytest.param(
            "d817767f-68b7-49a5-aa47-13419d41df0a", id="LogicalFunction"
        ),
    ],
)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)

    diagram = obj.context_diagram.render(None)

    diagram[uuid]
