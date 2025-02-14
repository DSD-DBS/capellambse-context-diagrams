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

TEST_REALIZATION_DATA_ROOT = TEST_ELK_INPUT_ROOT / "realization_views"
TEST_REALIZATION_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "realization_views"
TEST_FNC_UUID = "beaf5ba4-8fa9-4342-911f-0266bb29be45"
TEST_CMP_UUID = "b9f9a83c-fb02-44f7-9123-9d86326de5f1"
TEST_REALIZATION_SET = [
    pytest.param(
        (
            TEST_FNC_UUID,
            "fnc_realization_view.json",
            {"display_symbols_as_boxes": True},
        ),
        id="Function",
    ),
    pytest.param(
        (TEST_CMP_UUID, "cmp_realization_view.json", {}), id="Component"
    ),
]


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_collecting(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    file_path = TEST_REALIZATION_DATA_ROOT / params[1]
    expected_edges_file = TEST_REALIZATION_DATA_ROOT / (
        file_path.stem + "_edges.json"
    )
    expected_edges = expected_edges_file.read_text(encoding="utf8")

    def extra_assert(edges, expected_edges) -> bool:
        edges_list = [edge.model_dump(exclude_defaults=True) for edge in edges]
        return json.loads(expected_edges) == {"edges": edges_list}

    (result, edges), expected = generic_collecting_test(
        model,
        params,
        TEST_REALIZATION_DATA_ROOT,
        "realization_view",
    )

    assert compare_elk_input_data(result, expected)
    assert extra_assert(edges, expected_edges)


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_layouting(params: tuple[str, str, dict[str, t.Any]]):
    generic_layouting_test(
        params, TEST_REALIZATION_DATA_ROOT, TEST_REALIZATION_LAYOUT_ROOT
    )


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_serializing(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    generic_serializing_test(
        model, params, TEST_REALIZATION_LAYOUT_ROOT, "realization_view"
    )


@pytest.mark.parametrize(
    ("uuid", "search_direction", "show_owners"),
    [(TEST_FNC_UUID, "ABOVE", True), (TEST_CMP_UUID, "BELOW", False)],
)
@pytest.mark.parametrize(
    "layer_sizing", ["WIDTH", "UNION", "HEIGHT", "INDIVIDUAL"]
)
def test_realization_view_renders_with_additional_params(
    model: capellambse.MelodyModel,
    search_direction: str,
    show_owners: bool,
    layer_sizing: str,
    uuid: str,
):
    obj = model.by_uuid(uuid)

    diag = obj.realization_view

    assert diag.render(
        "svgdiagram",
        depth=3,
        search_direction=search_direction,
        show_owners=show_owners,
        layer_sizing=layer_sizing,
    )
