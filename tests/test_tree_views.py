# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs, context

from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    remove_ids_from_elk_layout,
    remove_sizes,
)

TEST_TREE_DATA_ROOT = TEST_ELK_INPUT_ROOT / "tree_views"
TEST_TREE_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "tree_views"
CLASS_UUID = "b7c7f442-377f-492c-90bf-331e66988bda"
TEST_TREE_SET = [
    pytest.param((CLASS_UUID, "tree_view.json"), id="Tree View"),
]


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_collecting(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    diag = obj.tree_view
    elk_data_file_path = TEST_TREE_DATA_ROOT / elk_data_filename
    data = elk_data_file_path.read_text(encoding="utf8")
    expected = _elkjs.ELKInputData.model_validate_json(data)
    legend_data = (
        TEST_TREE_DATA_ROOT / (elk_data_file_path.stem + "_legend.json")
    ).read_text(encoding="utf8")
    expected_legend = _elkjs.ELKInputData.model_validate_json(legend_data)

    _ = diag.elk_input_data({})
    elk_input, legend = diag._elk_input_data

    assert remove_sizes(elk_input) == remove_sizes(expected)
    assert remove_sizes(legend) == remove_sizes(expected_legend)


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_layouting(params: tuple[str, str]):
    _, elk_data_filename = params
    elk_data_file_path = TEST_TREE_DATA_ROOT / elk_data_filename
    test_data = elk_data_file_path.read_text(encoding="utf8")
    data = _elkjs.ELKInputData.model_validate_json(test_data)
    expected_legend = (
        TEST_TREE_DATA_ROOT / (elk_data_file_path.stem + "_legend.json")
    ).read_text(encoding="utf8")
    legend_data = _elkjs.ELKInputData.model_validate_json(expected_legend)
    elk_layout_file_path = TEST_TREE_LAYOUT_ROOT / elk_data_filename
    expected_layout_data = elk_layout_file_path.read_text(encoding="utf8")
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)
    expected_legend_layout_data = (
        TEST_TREE_LAYOUT_ROOT / (elk_layout_file_path.stem + "_legend.json")
    ).read_text(encoding="utf8")
    expected_legend_layout = _elkjs.ELKOutputData.model_validate_json(
        expected_legend_layout_data
    )

    layout = context.try_to_layout(data)
    legend_layout = context.try_to_layout(legend_data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )
    assert remove_ids_from_elk_layout(
        legend_layout
    ) == remove_ids_from_elk_layout(expected_legend_layout)


@pytest.mark.parametrize("params", TEST_TREE_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    diag = obj.tree_view
    layout_data = (TEST_TREE_LAYOUT_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

    diag.serializer.make_diagram(layout)


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
