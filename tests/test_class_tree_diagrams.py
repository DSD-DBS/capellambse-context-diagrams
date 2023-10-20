# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest

CLASS_UUID = "b7c7f442-377f-492c-90bf-331e66988bda"


@pytest.mark.parametrize("fmt", ["svgdiagram", "svg", None])
def test_tree_diagram_gets_rendered_successfully(
    model: capellambse.MelodyModel, fmt: str
) -> None:
    obj = model.by_uuid(CLASS_UUID)

    diag = obj.tree_diagram

    assert diag.render(fmt)


@pytest.mark.parametrize("edgeRouting", ["SPLINE", "ORTHOGONAL", "POLYLINE"])
@pytest.mark.parametrize("direction", ["DOWN", "RIGHT"])
@pytest.mark.parametrize("partitioning", [True, False])
@pytest.mark.parametrize(
    "edgeLabelsSide", ["ALWAYS_DOWN", "DIRECTION_DOWN", "SMART_DOWN"]
)
def test_tree_diagram_renders_with_additional_params(
    model: capellambse.MelodyModel,
    edgeRouting: str,
    direction: str,
    partitioning: bool,
    edgeLabelsSide: str,
) -> None:
    obj = model.by_uuid(CLASS_UUID)

    diag = obj.tree_diagram

    assert diag.render(
        "svgdiagram",
        edgeRouting=edgeRouting,
        direction=direction,
        partitioning=partitioning,
        edgeLabelsSide=edgeLabelsSide,
    )
