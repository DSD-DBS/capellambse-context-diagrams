# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize("uuid", ["5c55b11b-4911-40fb-9c4c-f1363dad846e"])
@pytest.mark.parametrize("fmt", ["svgdiagram", "svg", None])
def test_exchange_item_relation_views(
    model: capellambse.MelodyModel, uuid: str, fmt: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.cable_tree
    diag.render("svgdiagram").save(pretty=True)

    assert diag.render(fmt)
