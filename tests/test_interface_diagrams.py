# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid",
    [
        # pytest.param("3c9764aa-4981-44ef-8463-87a053016635", id="OA"),
        pytest.param("86a1afc2-b7fd-4023-bbd5-ab44f5dc2c28", id="SA"),
        pytest.param("3ef23099-ce9a-4f7d-812f-935f47e7938d", id="LA"),
    ],
)
def test_interface_diagrams_get_rendered(
    model: capellambse.MelodyModel, uuid: str, tmp_path: pathlib.Path
) -> None:
    obj = model.by_uuid(uuid)
    filename = tmp_path / "tmp.svg"

    diag = obj.context_diagram
    diag.render("svgdiagram").save_drawing(filename=filename)

    assert diag.nodes
