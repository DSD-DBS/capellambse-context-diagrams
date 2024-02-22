# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

import capellambse
import pytest

CLASS_UUID = "b7c7f442-377f-492c-90bf-331e66988bda"


@pytest.mark.parametrize("fmt", ["svgdiagram", "svg", None])
def test_tree_view_gets_rendered_successfully(
    model: capellambse.MelodyModel, fmt: str
) -> None:
    obj = model.by_uuid(CLASS_UUID)

    diag = obj.tree_view

    assert diag.render(fmt)


@pytest.mark.parametrize("edgeRouting", ["SPLINE", "ORTHOGONAL", "POLYLINE"])
@pytest.mark.parametrize("direction", ["DOWN", "RIGHT"])
@pytest.mark.parametrize("partitioning", [True, False])
@pytest.mark.parametrize(
    "edgeLabelsSide", ["ALWAYS_DOWN", "DIRECTION_DOWN", "SMART_DOWN"]
)
@pytest.mark.parametrize("depth", [None, 1])
@pytest.mark.parametrize("super", ["ALL", "ROOT"])
@pytest.mark.parametrize("sub", ["ALL", "ROOT"])
def test_tree_view_renders_with_additional_params(
    model: capellambse.MelodyModel,
    edgeRouting: str,
    direction: str,
    partitioning: bool,
    edgeLabelsSide: str,
    depth: int,
    super: t.Literal["ALL"] | t.Literal["ROOT"],
    sub: t.Literal["ALL"] | t.Literal["ROOT"],
) -> None:
    obj = model.by_uuid(CLASS_UUID)

    diag = obj.tree_view

    assert diag.render(
        "svgdiagram",
        edgeRouting=edgeRouting,
        direction=direction,
        partitioning=partitioning,
        edgeLabelsSide=edgeLabelsSide,
        depth=depth,
        super=super,
        sub=sub,
    )
