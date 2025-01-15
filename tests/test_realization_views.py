# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest

TEST_FNC_UUID = "beaf5ba4-8fa9-4342-911f-0266bb29be45"
TEST_CMP_UUID = "b9f9a83c-fb02-44f7-9123-9d86326de5f1"


@pytest.mark.parametrize("uuid", [TEST_FNC_UUID, TEST_CMP_UUID])
def test_realization_view_gets_rendered_successfully(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.realization_view

    assert diag.render("svgdiagram")


@pytest.mark.parametrize(
    ("uuid", "search_direction", "show_owners"),
    [(TEST_FNC_UUID, "ABOVE", True), (TEST_CMP_UUID, "BELOW", False)],
)
@pytest.mark.parametrize(
    "layer_sizing", ["WIDTH", "UNION", "HEIGHT", "INDIVIDUAL"]
)
def test_realization_view_renders_with_additional_params(
    model: capellambse.MelodyModel,
    search_direction: str,
    show_owners: bool,
    layer_sizing: str,
    uuid: str,
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.realization_view

    assert diag.render(
        "svgdiagram",
        depth=3,
        search_direction=search_direction,
        show_owners=show_owners,
        layer_sizing=layer_sizing,
    )
