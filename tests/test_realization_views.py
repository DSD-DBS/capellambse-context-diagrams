# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import json
from unittest import mock

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs, context

from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    remove_ids_from_elk_layout,
    text_size_mocker,
)

TEST_REALIZATION_DATA_ROOT = TEST_ELK_INPUT_ROOT / "realization_views"
TEST_REALIZATION_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "realization_views"
TEST_FNC_UUID = "beaf5ba4-8fa9-4342-911f-0266bb29be45"
TEST_CMP_UUID = "b9f9a83c-fb02-44f7-9123-9d86326de5f1"
TEST_REALIZATION_SET = [
    pytest.param((TEST_FNC_UUID, "fnc_realization_view.json"), id="Function"),
    pytest.param((TEST_CMP_UUID, "cmp_realization_view.json"), id="Component"),
]


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_collecting(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    elk_data_file_path = TEST_REALIZATION_DATA_ROOT / elk_data_filename
    data = elk_data_file_path.read_text(encoding="utf8")
    expected = _elkjs.ELKInputData.model_validate_json(data)
    expected_edges = (
        TEST_REALIZATION_DATA_ROOT / (elk_data_file_path.stem + "_edges.json")
    ).read_text(encoding="utf8")

    with mock.patch("capellambse.helpers.get_text_extent") as mock_ext:
        mock_ext.side_effect = text_size_mocker
        elk_input, edges = obj.realization_view.elk_input_data({})

    assert elk_input.model_dump(exclude_defaults=True) == expected.model_dump(
        exclude_defaults=True
    )
    assert json.loads(expected_edges) == {
        "edges": [edge.model_dump(exclude_defaults=True) for edge in edges]
    }


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_layouting(params: tuple[str, str]):
    _, elk_data_filename = params
    test_data = (TEST_REALIZATION_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    data = _elkjs.ELKInputData.model_validate_json(test_data)
    expected_layout_data = (
        TEST_REALIZATION_LAYOUT_ROOT / elk_data_filename
    ).read_text(encoding="utf8")
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)

    layout = context.try_to_layout(data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )


@pytest.mark.parametrize("params", TEST_REALIZATION_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    diag = obj.realization_view
    diag._display_symbols_as_boxes = True
    layout_data = (TEST_REALIZATION_LAYOUT_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

    diag.serializer.make_diagram(layout)


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
