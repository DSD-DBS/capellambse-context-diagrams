# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import json

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs, context

from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    remove_ids_from_elk_layout,
)

TEST_DATA_FLOW_DATA_ROOT = TEST_ELK_INPUT_ROOT / "data_flow_views"
TEST_DATA_FLOW_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "data_flow_views"
TEST_DATA_FLOW_SET = [
    pytest.param(
        ("3b83b4ba-671a-4de8-9c07-a5c6b1d3c422", "opcap_data_flow.json"),
        id="OperationalCapability",
    ),
    pytest.param(
        ("9390b7d5-598a-42db-bef8-23677e45ba06", "cap_data_flow.json"),
        id="Capability",
    ),
]


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_collecting(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    expected = (TEST_DATA_FLOW_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )

    _ = (diag := obj.data_flow_view).elk_input_data({})
    elk_input = diag._elk_input_data.model_dump(exclude_defaults=True)

    assert elk_input == json.loads(expected)


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_layouting(params: tuple[str, str]):
    _, elk_data_filename = params
    test_data = (TEST_DATA_FLOW_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    expected_layout_data = (
        TEST_DATA_FLOW_LAYOUT_ROOT / elk_data_filename
    ).read_text(encoding="utf8")
    data = _elkjs.ELKInputData.model_validate_json(test_data)
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)

    layout = context.try_to_layout(data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    diag = obj.data_flow_view

    layout_data = (TEST_DATA_FLOW_LAYOUT_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

    diag.serializer.make_diagram(layout)
