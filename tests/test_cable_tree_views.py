# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

import capellambse
import pytest

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import (  # type: ignore[import-untyped]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    compare_elk_input_data,
    generic_collecting_test,
    generic_layouting_test,
    generic_serializing_test,
)

TEST_CABLE_TREE_DATA_ROOT = TEST_ELK_INPUT_ROOT / "cable_trees"
TEST_CABLE_TREE_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "cable_trees"
TEST_SET = [
    pytest.param(
        (
            "5c55b11b-4911-40fb-9c4c-f1363dad846e",
            "full_cable_tree.json",
            {"port_label_position": "OUTSIDE"},
        ),
        id="Full Tree",
    ),
    pytest.param(
        (
            "39e96ffc-2f32-41b9-b406-ba82c78fe451",
            "inside_cable_tree.json",
            {"port_label_position": "OUTSIDE"},
        ),
        id="Inside Tree",
    ),
    pytest.param(
        (
            "6c607b75-504a-4d68-966b-0982fde3275e",
            "outside_cable_tree.json",
            {"port_label_position": "OUTSIDE"},
        ),
        id="Outside Tree",
    ),
]


@pytest.mark.parametrize("params", TEST_SET)
def test_collecting(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    result, expected = generic_collecting_test(
        model, params, TEST_CABLE_TREE_DATA_ROOT, "cable_tree"
    )

    assert compare_elk_input_data(result, expected)


@pytest.mark.parametrize("params", TEST_SET)
def test_layouting(params: tuple[str, str, dict[str, t.Any]]):
    generic_layouting_test(
        params, TEST_CABLE_TREE_DATA_ROOT, TEST_CABLE_TREE_LAYOUT_ROOT
    )


@pytest.mark.parametrize("params", TEST_SET)
def test_serializing(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    generic_serializing_test(
        model, params, TEST_CABLE_TREE_LAYOUT_ROOT, "cable_tree"
    )
