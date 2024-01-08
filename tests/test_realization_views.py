# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest

TEST_FNC_UUID = "beaf5ba4-8fa9-4342-911f-0266bb29be45"
TEST_CMP_UUID = "b9f9a83c-fb02-44f7-9123-9d86326de5f1"


@pytest.mark.parametrize("uuid", [TEST_FNC_UUID, TEST_CMP_UUID])
@pytest.mark.parametrize("fmt", ["svgdiagram", "svg", None])
def test_tree_view_gets_rendered_successfully(
    model: capellambse.MelodyModel, fmt: str, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.realization_view

    assert diag.render(fmt)


@pytest.mark.parametrize("uuid", [TEST_FNC_UUID, TEST_CMP_UUID])
@pytest.mark.parametrize("depth", list(range(1, 4)))
@pytest.mark.parametrize("search_direction", ["ABOVE", "BELOW"])
@pytest.mark.parametrize("show_owners", [True, False])
def test_tree_view_renders_with_additional_params(
    model: capellambse.MelodyModel,
    depth: int,
    search_direction: str,
    show_owners: bool,
    uuid: str,
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.realization_view

    assert diag.render(
        "svgdiagram",
        depth=depth,
        search_direction=search_direction,
        show_owners=show_owners,
    )
