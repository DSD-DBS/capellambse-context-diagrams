# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import capellambse.metamodel as mm
import pytest

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import SYSTEM_ANALYSIS_PARAMS  # type: ignore[import-untyped]

TEST_TYPES = (
    mm.oa.OperationalCapability,
    mm.sa.Capability,
    mm.sa.Mission,
    mm.la.CapabilityRealization,
)
LA_AND_PA_CAPS = [
    pytest.param(
        "33ca2414-e82b-4b9b-a177-772726b68ba0", id="CapabilityRealization - LA"
    ),
    # pytest.param(
    #     "da08ddb6-92ba-4c3b-956a-017424dbfe85", id="CapabilityRealization - PA"
    # ),
]


@pytest.mark.parametrize("uuid", SYSTEM_ANALYSIS_PARAMS + LA_AND_PA_CAPS)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)
    assert isinstance(obj, TEST_TYPES), "Precondition failed"

    diag = obj.context_diagram
    obj.context_diagram.render("svgdiagram").save(pretty=True)

    assert diag.nodes
