# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

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

TEST_DATA_FLOW_DATA_ROOT = TEST_ELK_INPUT_ROOT / "data_flow_views"
TEST_DATA_FLOW_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "data_flow_views"
RENDER_PARAMS = {
    "display_symbols_as_boxes": True,
    "display_parent_relation": False,
    "edge_direction": "NONE",
    "mode": "WHITEBOX",
}
TEST_DATA_FLOW_SET = [
    pytest.param(
        (
            "3b83b4ba-671a-4de8-9c07-a5c6b1d3c422",
            "opcap_data_flow.json",
            RENDER_PARAMS,
        ),
        id="OperationalCapability",
    ),
    pytest.param(
        (
            "9390b7d5-598a-42db-bef8-23677e45ba06",
            "cap_data_flow.json",
            RENDER_PARAMS,
        ),
        id="Capability",
    ),
]


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_collecting(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    result, expected = generic_collecting_test(
        model, params, TEST_DATA_FLOW_DATA_ROOT, "data_flow_view"
    )

    assert compare_elk_input_data(result, expected)


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_layouting(params: tuple[str, str, dict[str, t.Any]]):
    generic_layouting_test(
        params, TEST_DATA_FLOW_DATA_ROOT, TEST_DATA_FLOW_LAYOUT_ROOT
    )


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_serializing(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    generic_serializing_test(
        model, params, TEST_DATA_FLOW_LAYOUT_ROOT, "data_flow_view"
    )
