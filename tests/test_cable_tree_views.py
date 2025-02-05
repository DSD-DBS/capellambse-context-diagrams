# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs, context

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    remove_ids_from_elk_layout,
    text_size_mocker,
)

TEST_CABLE_TREE_DATA_ROOT = TEST_ELK_INPUT_ROOT / "cable_trees"
TEST_CABLE_TREE_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "cable_trees"
TEST_SET = [
    pytest.param(
        ("5c55b11b-4911-40fb-9c4c-f1363dad846e", "full_cable_tree.json"),
        id="Full Tree",
    ),
    pytest.param(
        ("39e96ffc-2f32-41b9-b406-ba82c78fe451", "inside_cable_tree.json"),
        id="Inside Tree",
    ),
    pytest.param(
        (
            "6c607b75-504a-4d68-966b-0982fde3275e",
            "outside_cable_tree.json",
        ),
        id="Outside Tree",
    ),
]


@pytest.mark.parametrize("params", TEST_SET)
def test_collecting(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_path = params
    obj = model.by_uuid(uuid)
    data = (TEST_CABLE_TREE_DATA_ROOT / elk_data_path).read_text(
        encoding="utf8"
    )
    expected = _elkjs.ELKInputData.model_validate_json(data)

    with mock.patch("capellambse.helpers.get_text_extent") as mock_ext:
        mock_ext.side_effect = text_size_mocker
        _ = (diag := obj.context_diagram).elk_input_data({})

    assert diag._elk_input_data.model_dump(
        exclude_defaults=True
    ) == expected.model_dump(exclude_defaults=True)


@pytest.mark.parametrize("params", TEST_SET)
def test_layouting(params: tuple[str, str]):
    _, elk_data_filename = params
    test_data = (TEST_CABLE_TREE_DATA_ROOT / elk_data_filename).read_text(
        encoding="utf8"
    )
    expected_layout_data = (
        TEST_CABLE_TREE_LAYOUT_ROOT / elk_data_filename
    ).read_text(encoding="utf8")
    data = _elkjs.ELKInputData.model_validate_json(test_data)
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)

    layout = context.try_to_layout(data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )


@pytest.mark.parametrize("params", TEST_SET)
def test_serializing(model: capellambse.MelodyModel, params: tuple[str, str]):
    uuid, elk_data_path = params
    diag = model.by_uuid(uuid).cable_tree
    diag._display_port_labels = True
    diag._port_label_position = _elkjs.PORT_LABEL_POSITION.OUTSIDE.name
    layout_data = (TEST_CABLE_TREE_LAYOUT_ROOT / elk_data_path).read_text(
        encoding="utf8"
    )
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

    diag.serializer.make_diagram(layout)
