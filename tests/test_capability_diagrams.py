# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import json

import capellambse
import capellambse.metamodel as mm
import pytest

from capellambse_context_diagrams import _elkjs, context

from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    remove_ids_from_elk_layout,
)

TEST_TYPES = (mm.oa.OperationalCapability, mm.sa.Capability, mm.sa.Mission)
TEST_CONTEXT_DATA_ROOT = TEST_ELK_INPUT_ROOT / "context_diagrams"
TEST_CONTEXT_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "context_diagrams"
TEST_CONTEXT_SET = [
    pytest.param(
        ("da08ddb6-92ba-4c3b-956a-017424dbfe85", "opcap_context_diagram.json"),
        id="OperationalCapability",
    ),
    pytest.param(
        ("9390b7d5-598a-42db-bef8-23677e45ba06", "cap_context_diagram.json"),
        id="Capability",
    ),
    pytest.param(
        ("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6", "mis_context_diagram.json"),
        id="Mission",
    ),
]


@pytest.mark.parametrize("params", TEST_CONTEXT_SET)
def test_collecting(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    assert isinstance(obj, TEST_TYPES), "Precondition failed"

    expected = (TEST_CONTEXT_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )

    _ = (diag := obj.context_diagram).elk_input_data({})
    elk_input = diag._elk_input_data.model_dump(exclude_defaults=True)

    assert elk_input == json.loads(expected)


@pytest.mark.parametrize("params", TEST_CONTEXT_SET)
def test_layouting(params: tuple[str, str]):
    _, elk_data_filename = params
    test_data = (TEST_CONTEXT_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    expected_layout_data = (
        TEST_CONTEXT_LAYOUT_ROOT / elk_data_filename
    ).read_text(encoding="utf8")
    data = _elkjs.ELKInputData.model_validate_json(test_data)
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)

    layout = context.try_to_layout(data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )


@pytest.mark.parametrize("params", TEST_CONTEXT_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_filename = params
    obj = model.by_uuid(uuid)
    assert isinstance(obj, TEST_TYPES), "Precondition failed"
    diag = obj.context_diagram
    diag._display_symbols_as_boxes = False
    layout_data = (TEST_CONTEXT_LAYOUT_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

    diag.serializer.make_diagram(layout)
