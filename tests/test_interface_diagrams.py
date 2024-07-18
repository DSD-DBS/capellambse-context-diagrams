# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest

TEST_INTERFACE_UUID = "2f8ed849-fbda-4902-82ec-cbf8104ae686"


@pytest.mark.parametrize(
    "uuid",
    [
        # pytest.param("3c9764aa-4981-44ef-8463-87a053016635", id="OA"),
        pytest.param("86a1afc2-b7fd-4023-bbd5-ab44f5dc2c28", id="SA"),
        pytest.param("3ef23099-ce9a-4f7d-812f-935f47e7938d", id="LA"),
    ],
)
def test_interface_diagrams_get_rendered(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram

    assert diag.nodes


def test_interface_diagrams_with_nested_components_and_functions(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram

    assert diag.nodes


def test_interface_diagram_with_included_interface(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram.render(None, include_interface=False)

    with pytest.raises(KeyError):
        diag[TEST_INTERFACE_UUID]  # pylint: disable=pointless-statement


def test_interface_diagram_with_hide_functions(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram.render(None, hide_functions=True)

    for uuid in (
        "fbfb2b20-b711-4211-9b75-25e38390cdbc",  # LogicalFunction
        "2b30434f-a087-40f1-917b-c9d0af15be23",  # FunctionalExchange
    ):
        with pytest.raises(KeyError):
            diag[uuid]  # pylint: disable=pointless-statement


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
