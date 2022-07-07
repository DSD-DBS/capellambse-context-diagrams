# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest
from capellambse.model.layers import ctx, oa

TEST_TYPES = (oa.OperationalCapability, ctx.Capability, ctx.Mission)


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(
            "da08ddb6-92ba-4c3b-956a-017424dbfe85", id="OperationalCapability"
        ),
        pytest.param("9390b7d5-598a-42db-bef8-23677e45ba06", id="Capability"),
        pytest.param("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6", id="Mission"),
    ],
)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram

    assert isinstance(obj, TEST_TYPES)
    assert diag.nodes
