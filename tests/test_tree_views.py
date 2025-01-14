# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

import capellambse
import pytest

CLASS_UUID = "b7c7f442-377f-492c-90bf-331e66988bda"


def test_tree_view_gets_rendered_successfully(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(CLASS_UUID)

    diag = obj.tree_view

    assert diag.render("svgdiagram")


@pytest.mark.parametrize(
    ("edgeRouting", "direction", "edgeLabelsSide"),
    [
        ("SPLINE", "DOWN", "ALWAYS_DOWN"),
        ("ORTHOGONAL", "RIGHT", "DIRECTION_DOWN"),
        ("POLYLINE", "RIGHT", "SMART_DOWN"),
    ],
)
@pytest.mark.parametrize(
    ("super", "sub"), [("ALL", "ALL"), ("ALL", "ROOT"), ("ROOT", "ROOT")]
)
@pytest.mark.parametrize("partitioning", [True, False])
@pytest.mark.parametrize("depth", [None, 1])
def test_tree_view_renders_with_additional_params(
    model: capellambse.MelodyModel,
    edgeRouting: str,
    direction: str,
    partitioning: bool,
    edgeLabelsSide: str,
    depth: int,
    super: t.Literal["ALL", "ROOT"],
    sub: t.Literal["ALL", "ROOT"],
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
