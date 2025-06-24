# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

import capellambse
import pytest

from .conftest import (  # type: ignore[import-not-found]
    TEST_ELK_INPUT_ROOT,
    TEST_ELK_LAYOUT_ROOT,
    compare_elk_input_data,
    generic_collecting_test,
    generic_layouting_test,
    generic_serializing_test,
)

TEST_DATA_FLOW_DATA_ROOT = TEST_ELK_INPUT_ROOT / "data_flow_views"
TEST_DATA_FLOW_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "data_flow_views"
TEST_OCAP_UUID = "3b83b4ba-671a-4de8-9c07-a5c6b1d3c422"
TEST_CAP_UUID = "9390b7d5-598a-42db-bef8-23677e45ba06"
TEST_CR_UUID = "72147e11-70df-499b-a339-b81722271f1a"

TEST_DATA_FLOW_SET = [
    pytest.param(
        (TEST_OCAP_UUID, "opcap_data_flow.json", {}),
        id="OperationalCapability",
    ),
    pytest.param(
        (
            TEST_OCAP_UUID,
            "opcap_without_entities_data_flow.json",
            {"display_parent_relation": False},
        ),
        id="OperationalCapability without entities",
    ),
    pytest.param((TEST_CAP_UUID, "cap_data_flow.json", {}), id="Capability"),
    pytest.param(
        (
            TEST_CAP_UUID,
            "cap_without_components_data_flow.json",
            {"display_parent_relation": False},
        ),
        id="Capability without entities",
    ),
    pytest.param(
        (TEST_CR_UUID, "cap_realization_data_flow.json", {}),
        id="CapabilityRealization",
    ),
    pytest.param(
        (
            TEST_CR_UUID,
            "cap_realization_without_components_data_flow.json",
            {"display_parent_relation": False},
        ),
        id="CapabilityRealization without entities",
    ),
]


@pytest.mark.parametrize("params", TEST_DATA_FLOW_SET)
def test_collecting(
    model: capellambse.MelodyModel, params: tuple[str, str, dict[str, t.Any]]
):
    result, expected = generic_collecting_test(
        model, params, TEST_DATA_FLOW_DATA_ROOT, "data_flow_view"
    )

    compare_elk_input_data(result, expected)


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
