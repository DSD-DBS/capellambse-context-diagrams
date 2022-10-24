# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import capellambse
import pytest

TEST_CAP_SIZING_UUID = "b996a45f-2954-4fdd-9141-7934e7687de6"
TEST_HUMAN_ACTOR_SIZING_UUID = "e95847ae-40bb-459e-8104-7209e86ea2d1"
TEST_ACTOR_SIZING_UUID = "6c8f32bf-0316-477f-a23b-b5239624c28d"


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param("e37510b9-3166-4f80-a919-dfaac9b696c7", id="Entity"),
        pytest.param("8bcb11e6-443b-4b92-bec2-ff1d87a224e7", id="Activity"),
        pytest.param(
            "344a405e-c7e5-4367-8a9a-41d3d9a27f81", id="SystemComponent"
        ),
        pytest.param(
            "230c4621-7e0a-4d0a-9db2-d4ba5e97b3df", id="SystemComponent Root"
        ),
        pytest.param(
            "a5642060-c9cc-4d49-af09-defaa3024bae", id="SystemFunction"
        ),
        pytest.param(
            "f632888e-51bc-4c9f-8e81-73e9404de784", id="LogicalComponent"
        ),
        pytest.param(
            "7f138bae-4949-40a1-9a88-15941f827f8c", id="LogicalFunction"
        ),
        pytest.param(
            "b51ccc6f-5f96-4e28-b90e-72463a3b50cf", id="PhysicalNodeComponent"
        ),
        pytest.param(
            "c78b5d7c-be0c-4ed4-9d12-d447cb39304e",
            id="PhysicalBehaviorComponent",
        ),
    ],
)
def test_context_diagrams(
    model: capellambse.MelodyModel, uuid: str, tmp_path: pathlib.Path
) -> None:
    obj = model.by_uuid(uuid)
    filename = tmp_path / "tmp.svg"

    diag = obj.context_diagram
    diag.render("svgdiagram").save_drawing(filename=filename)

    assert diag.nodes


@pytest.mark.parametrize(
    "diagram_elements",
    [
        pytest.param(
            [
                ("e9a6fd43-88d2-4832-91d5-595b6fbf613d", 42),
                ("a4f69ce4-2f3f-40d4-af58-423388df449f", 72),
                ("a07b7cb1-0424-4261-9980-504dd9c811d4", 72),
            ],
            id="Entity",
        ),
        pytest.param(
            [
                (TEST_ACTOR_SIZING_UUID, 37),
                (TEST_HUMAN_ACTOR_SIZING_UUID, 57),
                (TEST_CAP_SIZING_UUID, 92),
            ],
            id="Capability",
        ),
        pytest.param(
            [
                ("e1e48763-7479-4f3a-8134-c82bb6705d58", 98),
                ("8df45b70-15cc-4d3a-99e4-593516392c5a", 122),
                ("74af6883-25a0-446a-80f3-656f8a490b11", 122),
            ],
            id="LogicalComponent",
        ),
        pytest.param(
            [
                ("0c06cc88-8c77-46f2-8542-c08b1e8edd18", 86),
                ("9f1e1875-9ead-4af2-b428-c390786a436a", 86),
            ],
            id="LogicalFunction",
        ),
        pytest.param(
            [
                ("6241d0c5-65d2-4c0b-b79c-a2a8ed7273f6", 17),
                ("344a405e-c7e5-4367-8a9a-41d3d9a27f81", 17),
                ("230c4621-7e0a-4d0a-9db2-d4ba5e97b3df", 37),
            ],
            id="SystemComponent Root",
        ),
    ],
)
def test_context_diagrams_box_sizing(
    model: capellambse.MelodyModel, diagram_elements: list[tuple[str, int]]
) -> None:
    uuid, min_size = diagram_elements.pop()
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram
    diag.display_symbols_as_boxes = True
    adiag = diag.render(None)

    assert adiag[uuid].size.y >= min_size
    for uuid, min_size in diagram_elements:
        obj = model.by_uuid(uuid)

        assert adiag[uuid].size.y >= min_size


def test_context_diagrams_symbol_sizing(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_CAP_SIZING_UUID)

    adiag = obj.context_diagram.render(None)

    assert adiag[TEST_CAP_SIZING_UUID].size.y >= 92
    assert adiag[TEST_HUMAN_ACTOR_SIZING_UUID].size.y >= 57
    assert adiag[TEST_ACTOR_SIZING_UUID].size.y >= 37
