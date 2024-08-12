# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param("0ab202d7-6497-4b78-9d13-fd7c9a75486c", id="LA"),
    ],
)
def test_element_relation_views(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.element_relation_view
    diag.render("svgdiagram").save(pretty=True)

    assert diag.nodes
