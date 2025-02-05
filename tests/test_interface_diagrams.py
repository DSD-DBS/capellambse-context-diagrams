# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t
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

TEST_INTERFACE_UUID = "2f8ed849-fbda-4902-82ec-cbf8104ae686"
TEST_CABLE_UUID = "da949a89-23c0-4487-88e1-f14b33326570"
TEST_INTERFACE_DATA_ROOT = TEST_ELK_INPUT_ROOT / "interface_context"
TEST_INTERFACE_LAYOUT_ROOT = TEST_ELK_LAYOUT_ROOT / "interface_context"
TEST_INTERFACE_SET = [
    pytest.param(
        (
            "86a1afc2-b7fd-4023-bbd5-ab44f5dc2c28",
            "sa_interface_diagram.json",
            {"display_symbols_as_boxes": True},
        ),
        id="SA",
    ),
    pytest.param(
        (
            "3ef23099-ce9a-4f7d-812f-935f47e7938d",
            "la_interface_diagram.json",
            {},
        ),
        id="LA",
    ),
    pytest.param(
        (
            "25f46b82-1bb8-495a-b6bc-3ad086aad02e",
            "pa_interface_diagram.json",
            {},
        ),
        id="PA - ComponentExchange",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_outside_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "OUTSIDE",
            },
        ),
        id="PA - PhysicalLink",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_inside_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "INSIDE",
            },
        ),
        id="PA - PhysicalLink Port Labels Inside",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_next_to_port_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "NEXT_TO_PORT_IF_POSSIBLE",
            },
        ),
        id="PA - PhysicalLink Port Labels Next to Port",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_always_same_side_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "ALWAYS_SAME_SIDE",
            },
        ),
        id="PA - PhysicalLink Port Labels always same side",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_always_other_side_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "ALWAYS_OTHER_SAME_SIDE",
            },
        ),
        id="PA - PhysicalLink Port Labels always other side",
    ),
    pytest.param(
        (
            TEST_CABLE_UUID,
            "cable_interface_space_efficient_port_labels_diagram.json",
            {
                "display_symbols_as_boxes": True,
                "port_label_position": "SPACE_EFFICIENT",
            },
        ),
        id="PA - PhysicalLink Port Labels space efficient",
    ),
    pytest.param(
        (TEST_INTERFACE_UUID, "interface_nested_context_diagram.json", {}),
        id="Interface Nested Components",
    ),
    pytest.param(
        (
            TEST_INTERFACE_UUID,
            "interface_hidden_functions_context_diagram.json",
            {},
        ),
        id="Interface hidden functions",
    ),
]


class TestInterfaceDiagrams:
    @staticmethod
    @pytest.mark.parametrize("params", TEST_INTERFACE_SET)
    def test_collecting(
        model: capellambse.MelodyModel,
        params: tuple[str, str, dict[str, t.Any]],
    ):
        uuid, elk_data_filename, _ = params
        obj = model.by_uuid(uuid)
        diag = obj.context_diagram
        data = (TEST_INTERFACE_DATA_ROOT / elk_data_filename).read_text(
            encoding="utf8"
        )
        expected = _elkjs.ELKInputData.model_validate_json(data)

        with mock.patch("capellambse.helpers.get_text_extent") as mock_ext:
            mock_ext.side_effect = text_size_mocker
            _ = (diag := obj.context_diagram).elk_input_data({})

        assert diag._elk_input_data.model_dump(
            exclude_defaults=True
        ) == expected.model_dump(exclude_defaults=True)

    @staticmethod
    @pytest.mark.parametrize("params", TEST_INTERFACE_SET)
    def test_layouting(params: tuple[str, str, dict[str, t.Any]]):
        _, elk_data_filename, _ = params
        test_data = (TEST_INTERFACE_DATA_ROOT / elk_data_filename).read_text(
            encoding="utf8"
        )
        expected_layout_data = (
            TEST_INTERFACE_LAYOUT_ROOT / elk_data_filename
        ).read_text(encoding="utf8")
        data = _elkjs.ELKInputData.model_validate_json(test_data)
        expected = _elkjs.ELKOutputData.model_validate_json(
            expected_layout_data
        )

        layout = context.try_to_layout(data)

        assert remove_ids_from_elk_layout(
            layout
        ) == remove_ids_from_elk_layout(expected)

    @staticmethod
    @pytest.mark.parametrize("params", TEST_INTERFACE_SET)
    def test_serializing(
        model: capellambse.MelodyModel,
        params: tuple[str, str, dict[str, t.Any]],
    ):
        uuid, filename, render_params = params
        obj = model.by_uuid(uuid)
        diag = obj.context_diagram
        for key, value in render_params.items():
            setattr(diag, f"_{key}", value)

        layout_data = (TEST_INTERFACE_LAYOUT_ROOT / filename).read_text(
            encoding="utf8"
        )
        layout = _elkjs.ELKOutputData.model_validate_json(layout_data)

        diag.serializer.make_diagram(layout)


def test_interface_diagram_with_included_interface(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram.render(None, include_interface=False)

    with pytest.raises(KeyError):
        diag[TEST_INTERFACE_UUID]  # pylint: disable=pointless-statement


def test_interface_diagram_with_nested_functions(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)
    fex = model.by_uuid("2b30434f-a087-40f1-917b-c9d0af15be23")
    fnc = fex.target.owner
    obj.target.owner.allocated_functions.append(fnc)
    obj.allocated_functional_exchanges.append(fex)
    expected_uuids = {
        "f713ba11-b18c-48f8-aabf-5ee57d5c87b7",
        "7cd5ae5b-6de7-42f6-8a35-9375dd5bbde8",
    }

    diag = obj.context_diagram.render(None)

    assert {b.uuid for b in diag[fnc.uuid].children} >= expected_uuids
