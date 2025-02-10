# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import json
import typing as t

import capellambse
import pytest

from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    compare_elk_input_data,
    generic_collecting_test,
    generic_layouting_test,
    generic_serializing_test,
)

TEST_TREE_DATA_ROOT = TEST_ELK_INPUT_ROOT / "tree_views"
TEST_TREE_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "tree_views"
CLASS_UUID = "b7c7f442-377f-492c-90bf-331e66988bda"
TEST_TREE_SET = [
    pytest.param((CLASS_UUID, "tree_view.json", {}), id="Tree View"),
]


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_collecting(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    file_path = TEST_TREE_DATA_ROOT / params[1]
    expected_legend_file = TEST_TREE_DATA_ROOT / (
        file_path.stem + "_legend.json"
    )
    expected_legend = expected_legend_file.read_text(encoding="utf8")

    (result, legend), expected = generic_collecting_test(
        model, params, TEST_TREE_DATA_ROOT, "tree_view"
    )

    assert compare_elk_input_data(result, expected)
    assert legend.model_dump(exclude_defaults=True) == json.loads(
        expected_legend
    )


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_layouting(params: tuple[str, str, dict[str, t.Any]]):
    _, elk_data_filename, _ = params
    elk_data_file_path = TEST_TREE_DATA_ROOT / elk_data_filename

    generic_layouting_test(params, TEST_TREE_DATA_ROOT, TEST_TREE_LAYOUT_ROOT)
    generic_layouting_test(
        ("", elk_data_file_path.stem + "_legend.json", {}),
        TEST_TREE_DATA_ROOT,
        TEST_TREE_LAYOUT_ROOT,
    )


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    generic_serializing_test(model, params, TEST_TREE_LAYOUT_ROOT, "tree_view")


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
):
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
