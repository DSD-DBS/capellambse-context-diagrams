# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid,expected_labels",
    [
        pytest.param(
            "d817767f-68b7-49a5-aa47-13419d41df0a",
            [
                ["Really long label"],
                ["that needs"],
                ["wrapping else"],
                ["its parent box is"],
                ["also very long!"],
            ],
            id="LogicalFunction",
        ),
    ],
)
def test_context_diagrams(
    model: capellambse.MelodyModel, uuid: str, expected_labels: list[list[str]]
) -> None:
    obj = model.by_uuid(uuid)

    diagram = obj.context_diagram.render(None)
    labels = [label.labels for label in diagram[uuid].labels]

    assert labels == expected_labels
