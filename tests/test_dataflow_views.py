# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(
            "3b83b4ba-671a-4de8-9c07-a5c6b1d3c422", id="OperationalCapability"
        ),
        pytest.param("9390b7d5-598a-42db-bef8-23677e45ba06", id="Capability"),
    ],
)
def test_data_flow_views(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.data_flow_view

    assert diag.nodes
