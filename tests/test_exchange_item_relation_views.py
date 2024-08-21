# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize("uuid", ["0ab202d7-6497-4b78-9d13-fd7c9a75486c"])
@pytest.mark.parametrize("fmt", ["svgdiagram", "svg", None])
def test_exchange_item_relation_views(
    model: capellambse.MelodyModel, uuid: str, fmt: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.exchange_item_relation_view

    assert diag.render(fmt)
