# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import sys

import capellambse
import pytest

TEST_CAP_SIZING_UUID = "b996a45f-2954-4fdd-9141-7934e7687de6"
TEST_HUMAN_ACTOR_SIZING_UUID = "e95847ae-40bb-459e-8104-7209e86ea2d1"
TEST_ACTOR_SIZING_UUID = "6c8f32bf-0316-477f-a23b-b5239624c28d"
TEST_HIERARCHY_UUID = "16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb"
TEST_HIERARCHY_PARENTS_UUIDS = {
    "0d2edb8f-fa34-4e73-89ec-fb9a63001440",
    "99a1d711-74af-4db7-af08-4dbd91c281ce",
    "53558f58-270e-4206-8fc7-3cf9e788fac9",
}
TEST_ACTIVITY_UUIDS = {
    "097bb133-abf3-4df0-ae4e-a28378537691",
    "5cc0ba13-badb-40b5-9d4c-e4d7b964fb36",
    "c90f731b-0036-47e5-a455-9cf270d6880c",
}
TEST_FUNCTION_UUIDS = {
    "861b9be3-a7b2-4e1d-b34b-8e857062b3df",
    "f0bc11ba-89aa-4297-98d2-076440e9117f",
}
TEST_DERIVED_UUID = "dbd99773-efb6-4476-bf5c-270a61f18b09"
TEST_ENTITY_UUID = "e37510b9-3166-4f80-a919-dfaac9b696c7"
TEST_SYS_FNC_UUID = "a5642060-c9cc-4d49-af09-defaa3024bae"
TEST_DERIVATION_UUID = "4ec45aec-0d6a-411a-80ee-ebd3c1a53d2c"
TEST_PHYSICAL_PORT_UUID = "c403d4f4-9633-42a2-a5d6-9e1df2655146"


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(TEST_ENTITY_UUID, id="Entity"),
        pytest.param("8bcb11e6-443b-4b92-bec2-ff1d87a224e7", id="Activity"),
        pytest.param(
            "344a405e-c7e5-4367-8a9a-41d3d9a27f81", id="SystemComponent"
        ),
        pytest.param(
            "230c4621-7e0a-4d0a-9db2-d4ba5e97b3df", id="SystemComponent Root"
        ),
        pytest.param(TEST_SYS_FNC_UUID, id="SystemFunction"),
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
        pytest.param(TEST_PHYSICAL_PORT_UUID, id="PhysicalPort"),
    ],
)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram
    diag.render(None, display_parent_relation=False)

    assert diag.nodes


def test_context_is_collected_again_with_derivated(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_DERIVATION_UUID)

    diagram = obj.context_diagram.render(None)

    assert len(diagram) > 1


@pytest.mark.parametrize(
    "parameter",
    [
        "display_parent_relation",
        "display_symbols_as_boxes",
        "display_derived_interfaces",
        "slim_center_box",
    ],
)
@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(TEST_ENTITY_UUID, id="Entity"),
        pytest.param(TEST_SYS_FNC_UUID, id="SystemFunction"),
    ],
)
def test_context_diagrams_rerender_on_parameter_change(
    model: capellambse.MelodyModel, parameter: str, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram
    diag.render(None, **{parameter: True})
    diag.render(None, **{parameter: False})


@pytest.mark.parametrize(
    "diagram_elements",
    [
        pytest.param(
            [
                ("e9a6fd43-88d2-4832-91d5-595b6fbf613d", 42, 42),
                ("a4f69ce4-2f3f-40d4-af58-423388df449f", 72, 72),
                ("a07b7cb1-0424-4261-9980-504dd9c811d4", 72, 72),
            ],
            id="Entity",
        ),
        pytest.param(
            [
                (TEST_ACTOR_SIZING_UUID, 40, 40),
                (TEST_HUMAN_ACTOR_SIZING_UUID, 43, 43),
                (TEST_CAP_SIZING_UUID, 141, 141),
            ],
            id="Capability",
        ),
        pytest.param(
            [
                ("e1e48763-7479-4f3a-8134-c82bb6705d58", 126, 190),
                ("8df45b70-15cc-4d3a-99e4-593516392c5a", 154, 234),
                ("74af6883-25a0-446a-80f3-656f8a490b11", 266, 412),
            ],
            id="LogicalComponent",
        ),
        pytest.param(
            [
                ("0c06cc88-8c77-46f2-8542-c08b1e8edd18", 112, 168),
                ("9f1e1875-9ead-4af2-b428-c390786a436a", 112, 168),
            ],
            id="LogicalFunction",
        ),
        pytest.param(
            [
                ("6241d0c5-65d2-4c0b-b79c-a2a8ed7273f6", 36, 36),
                ("344a405e-c7e5-4367-8a9a-41d3d9a27f81", 40, 40),
                ("230c4621-7e0a-4d0a-9db2-d4ba5e97b3df", 42, 60),
            ],
            id="SystemComponent Root",
        ),
    ],
)
def test_context_diagrams_box_sizing(
    model: capellambse.MelodyModel,
    diagram_elements: list[tuple[str, int, int]],
) -> None:
    uuid, min_size, min_size_labels = diagram_elements.pop()
    obj = model.by_uuid(uuid)

    adiag = obj.context_diagram.render(
        None, display_symbols_as_boxes=True, display_port_labels=False
    )
    bdiag = obj.context_diagram.render(
        None, display_symbols_as_boxes=True, display_port_labels=True
    )

    assert adiag[uuid].size.y >= min_size
    assert bdiag[uuid].size.y >= min_size_labels
    for uuid, min_size, min_size_labels in diagram_elements:
        obj = model.by_uuid(uuid)

        assert adiag[uuid].size.y >= min_size
        assert bdiag[uuid].size.y >= min_size_labels


def test_context_diagrams_symbol_sizing(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_CAP_SIZING_UUID)

    adiag = obj.context_diagram.render(None)

    assert adiag[TEST_CAP_SIZING_UUID].size.y >= 92
    assert adiag[TEST_HUMAN_ACTOR_SIZING_UUID].size.y >= 57
    assert adiag[TEST_ACTOR_SIZING_UUID].size.y >= 37


def test_parent_relation_in_context_diagram(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_HIERARCHY_UUID)

    diag = obj.context_diagram
    hide_relation = diag.render(None, display_parent_relation=False)
    diag.invalidate_cache()
    display_relation = diag.render(None, display_parent_relation=True)

    for uuid in TEST_HIERARCHY_PARENTS_UUIDS:
        assert display_relation[uuid]

        with pytest.raises(KeyError):
            hide_relation[uuid]  # pylint: disable=pointless-statement


@pytest.mark.parametrize("uuid", TEST_ACTIVITY_UUIDS)
def test_context_diagram_of_allocated_activities(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram
    diag.display_parent_relation = True

    assert len(diag.nodes) > 1


@pytest.mark.parametrize("uuid", TEST_FUNCTION_UUIDS)
def test_context_diagram_of_allocated_functions(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram
    diag.display_parent_relation = True

    assert len(diag.nodes) > 1


def test_context_diagram_with_derived_interfaces(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid(TEST_DERIVED_UUID)

    context_diagram = obj.context_diagram
    derived_diagram = context_diagram.render(
        None, display_derived_interfaces=True
    )

    assert len(derived_diagram) > 5


@pytest.mark.parametrize(
    "uuid",
    [
        pytest.param(
            "fdb34c92-7c49-491d-bf11-dd139930786e", id="PhysicalNodeComponent"
        ),
        pytest.param(
            "313f48f4-fb7e-47a8-b28a-76440932fcb9",
            id="PhysicalBehaviorComponent",
        ),
    ],
)
def test_context_diagram_of_physical_node_component(
    model: capellambse.MelodyModel, uuid: str
) -> None:
    obj = model.by_uuid(uuid)

    diag = obj.context_diagram

    assert len(diag.nodes) > 1


def test_context_diagram_hide_direct_children(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid("eca84d5c-fdcd-4cbe-90d5-7d00a256c62b")
    expected_hidden_uuids = {
        "a34300ee-6e63-4c72-b210-2adee00478f8",
        "6a557565-c9d4-4216-8e9e-03539c0e6095",
        "32483de8-abd5-4e50-811b-407fad44defa",
        "e786b912-51ed-4bb8-b03c-acb05c48f0c8",
        "727b7d69-3cd2-45cc-b423-1e7b93c83f5b",
        "c0a2ae6d-ac5e-4a73-84ef-b7b9df344170",
        "3e66b559-eea0-40af-b18c-0328ee10add7",
        "1b978e1e-1368-44a2-a9e6-12818614b23e",  # Port
    }

    diag = obj.context_diagram
    grey = diag.render(None, hide_direct_children=True)
    diag.invalidate_cache()
    white = diag.render(None, hide_direct_children=False)

    assert not {element.uuid for element in grey} & expected_hidden_uuids
    assert {element.uuid for element in white} & expected_hidden_uuids


def test_context_diagram_detects_and_handles_cycles(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid("98bbf6ec-161a-4332-a95e-e6990df868ad")

    diag = obj.context_diagram

    assert diag.nodes


def test_context_diagram_display_unused_ports(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid("446d3f9f-644d-41ee-bd57-8ae0f7662db2")
    unused_port_uuid = "5cbc4d2d-1b9c-4e10-914e-44d4526e4a2f"

    adiag = obj.context_diagram.render(None, display_unused_ports=False)
    bdiag = obj.context_diagram.render(None, display_unused_ports=True)

    assert unused_port_uuid not in {element.uuid for element in adiag}
    assert unused_port_uuid in {element.uuid for element in bdiag}


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Wrong coordinates on Windows for some reason",
)
def test_serializer_handles_hierarchical_edges_correctly(
    model: capellambse.MelodyModel,
) -> None:
    obj = model.by_uuid("b87dab3f-b44e-46ff-bfbe-fb96fbafe008")
    edge_uuid = "1a302a4a-9839-4ba4-8296-f54b470b4e59"
    edge1_uuid = "43158e15-f8d1-49e3-bc01-7222edcbf839"

    adiag = obj.context_diagram.render(None)

    assert (231.35, 94) <= adiag[f"{edge_uuid}_j0"].center <= (235, 94)
    assert (405.25, 122) <= adiag[f"{edge1_uuid}_j1"].center <= (410, 122)
