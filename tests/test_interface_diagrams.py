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


def test_interface_diagrams_with_nested_components(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram

    assert diag.nodes


def test_interface_diagram_with_included_interface(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_INTERFACE_UUID)

    diag = obj.context_diagram.render(None, include_interface=True)

    assert diag[TEST_INTERFACE_UUID]
