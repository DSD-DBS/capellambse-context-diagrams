# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import capellambse.model as m
import pytest


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            "[SAB] Example Interface Context", id="Simple SAB diagram"
        ),
        pytest.param("[LAB] Hierarchy", id="Simple LAB diagram"),
        pytest.param(
            "[LAB] Hierarchy Function example", id="Nested LAB diagram"
        ),
        pytest.param(
            "[PAB] Sub-component Cable Tree", id="Simple PAB diagram"
        ),
        pytest.param(
            "[PAB] Example Physical Function Context Diagram",
            id="Nested PAB diagram",
        ),
    ],
)
def test_capability_and_mission_context_diagrams(
    model: capellambse.MelodyModel, name: str
) -> None:
    obj = model.diagrams.by_name(name)
    assert isinstance(obj, m.Diagram), "Precondition failed"

    diag = obj.auto_layout

    assert diag.nodes
