# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest

from capellambse_context_diagrams.builders import _makers


@pytest.mark.parametrize(
    ("uuid", "expected_labels"),
    [
        pytest.param(
            "d817767f-68b7-49a5-aa47-13419d41df0a",
            [
                "Really long label that needs",
                "wrapping else its parent box is",
                "also very long!",
            ],
            id="LogicalFunction",
        ),
    ],
)
def test_make_label_wraps_long_label(
    model: capellambse.MelodyModel, uuid: str, expected_labels: list[list[str]]
):
    obj = model.by_uuid(uuid)

    labels = _makers.make_label(obj.name, max_width=_makers.MAX_LABEL_WIDTH)

    actual = [label.text for label in labels]
    assert actual == expected_labels
