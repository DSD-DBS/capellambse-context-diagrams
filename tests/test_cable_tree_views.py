# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest


@pytest.mark.parametrize(
    "diagram_elements",
    [
        pytest.param(
            ("5c55b11b-4911-40fb-9c4c-f1363dad846e", 29), id="Full Tree"
        ),
        pytest.param(
            ("39e96ffc-2f32-41b9-b406-ba82c78fe451", 8), id="Inside Tree"
        ),
        pytest.param(
            ("6c607b75-504a-4d68-966b-0982fde3275e", 14), id="Outside Tree"
        ),
    ],
)
def test_cable_tree_views(
    model: capellambse.MelodyModel, diagram_elements: tuple[str, int]
) -> None:
    uuid, number_of_elements = diagram_elements
    obj = model.by_uuid(uuid)

    diag = obj.cable_tree

    assert len(diag.nodes) >= number_of_elements
