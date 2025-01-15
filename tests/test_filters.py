# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import typing as t

import capellambse.metamodel as mm
import pytest
from capellambse import MelodyModel, diagram

from capellambse_context_diagrams import context, filters

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import SYSTEM_ANALYSIS_PARAMS  # type: ignore[import-untyped]

EX_PTRN = re.compile(r"\[(.*?)\]")
CAP_EXPLOIT = "4513c8cd-b94b-4bde-bd00-4c18aaf600ff"
FNC_UUID = "a5642060-c9cc-4d49-af09-defaa3024bae"
INTERF_UUID = "9cbdd233-aff5-47dd-9bef-9be1277c77c3"
HIERARCHY_UUID = "16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb"

Types = list[mm.fa.FunctionalExchange | mm.fa.ComponentExchange]


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        (
            (
                "[CapabilityExploitation] to Capability"
                "(9390b7d5-598a-42db-bef8-23677e45ba06) from Affleck"
                "(da12377b-fb70-4441-8faa-3a5c153c5de2)"
            ),
            "[CapabilityExploitation] to Capability from Affleck",
        ),
        (None, "[CapabilityExploitation] to Capability"),
        ("", ""),
    ],
)
def test_uuid_filter(model: MelodyModel, label: str, expected: str) -> None:
    exploitation = model.by_uuid(CAP_EXPLOIT)

    assert filters.uuid_filter(exploitation, label) == expected


def start_filter_apply_test(
    model: MelodyModel, uuid: str, filter_name: str, **render_params: t.Any
) -> tuple[Types, diagram.Diagram]:
    """StartUp for every filter test case."""
    obj = model.by_uuid(uuid)
    diag: context.ContextDiagram = obj.context_diagram
    diag.filters.add(filter_name)
    edges = [
        elt
        for elt in diag.nodes
        if isinstance(elt, mm.fa.FunctionalExchange | mm.fa.ComponentExchange)
    ]
    return edges, diag.render(None, **render_params)


def get_ExchangeItems(edge: diagram.Edge) -> list[str]:
    if not edge.labels:
        return []
    label = edge.labels[0].label
    assert isinstance(label, str)
    match = EX_PTRN.match(label)
    if match is None:
        return []
    return match.group(1).split(", ")


def has_sorted_ExchangeItems(edge: diagram.Edge) -> bool:
    exitems = get_ExchangeItems(edge)
    return exitems == sorted(exitems)


@pytest.mark.parametrize("uuid", [FNC_UUID, INTERF_UUID])
def test_EX_ITEMS_is_applied(model: MelodyModel, uuid: str) -> None:
    edges, aird_diag = start_filter_apply_test(model, uuid, filters.EX_ITEMS)

    for edge in edges:
        aedge = aird_diag[edge.uuid]
        expected = [ex.name for ex in edge.exchange_items]

        assert isinstance(aedge, diagram.Edge)
        if aedge.labels:
            assert get_ExchangeItems(aedge) == expected


@pytest.mark.parametrize(
    ("sort", "uuid"), [(False, FNC_UUID), (True, INTERF_UUID)]
)
def test_context_diagrams_ExchangeItems_sorting(
    model: MelodyModel, sort: bool, uuid: str
) -> None:
    edges, aird_diag = start_filter_apply_test(
        model, uuid, filters.EX_ITEMS, sorted_exchangedItems=sort
    )

    for edge in edges:
        aedge = aird_diag[edge.uuid]
        assert isinstance(aedge, diagram.Edge)
        assert has_sorted_ExchangeItems(aedge)


@pytest.mark.parametrize("uuid", [FNC_UUID, INTERF_UUID])
def test_context_diagrams_SHOW_EX_ITEMS_is_applied(
    model: MelodyModel, uuid: str
) -> None:
    edges, aird_diag = start_filter_apply_test(
        model, uuid, filters.SHOW_EX_ITEMS
    )

    for edge in edges:
        aedge = aird_diag[edge.uuid]
        expected_label = edge.name
        eitems = ", ".join(exi.name for exi in edge.exchange_items)
        if eitems:
            expected_label += f" [{eitems}]"

        assert isinstance(aedge, diagram.Edge)
        assert len(aedge.labels) == 1
        assert isinstance(aedge.labels[0].label, str)
        assert aedge.labels[0].label == expected_label


@pytest.mark.parametrize("uuid", [FNC_UUID, INTERF_UUID])
def test_context_diagrams_FEX_OR_EX_ITEMS_is_applied(
    model: MelodyModel, uuid: str
) -> None:
    edges, aird_diag = start_filter_apply_test(
        model, uuid, filters.EX_ITEMS_OR_EXCH
    )

    for edge in edges:
        aedge = aird_diag[edge.uuid]

        assert isinstance(aedge, diagram.Edge)

        label = aedge.labels[0].label
        if edge.exchange_items:
            eitem_label_frag = ", ".join(
                exi.name for exi in edge.exchange_items
            )

            assert label == f"[{eitem_label_frag}]"
        else:
            assert label == edge.name

        assert len(aedge.labels) == 1


@pytest.mark.parametrize("uuid", SYSTEM_ANALYSIS_PARAMS)
def test_context_diagrams_SYSTEM_EX_RELABEL_is_applied(
    model: MelodyModel, uuid: str
) -> None:
    diag: context.ContextDiagram = model.by_uuid(uuid).context_diagram
    expected = {
        "« exploits »",
        "« extends »",
        "« specializes »",
        "« includes »",
        "« involves »",
    }

    diag.filters.add(filters.SYSTEM_EX_RELABEL)

    for element in diag.render(None):
        if isinstance(element, diagram.Edge):
            assert element.labels[0].label in expected


def test_context_diagrams_NO_UUID_is_applied(model: MelodyModel) -> None:
    obj = model.by_uuid("9390b7d5-598a-42db-bef8-23677e45ba06")
    diag: context.ContextDiagram = obj.context_diagram

    diag.filters.clear()
    diag.filters.add(filters.NO_UUID)
    aird_diag = diag.render(None)
    aedge = aird_diag[CAP_EXPLOIT]

    assert isinstance(aedge, diagram.Edge)
    assert aedge.labels[0].label == "[CapabilityExploitation] to Capability"


def test_context_diagrams_no_edgelabels_render_param_is_applied(
    model: MelodyModel,
) -> None:
    obj = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae")
    diag: context.ContextDiagram = obj.context_diagram

    adiag = diag.render(None, no_edgelabels=True)

    for aedge in adiag:
        if isinstance(aedge, diagram.Edge):
            assert not aedge.labels


def test_context_diagrams_display_port_labels_render_param_is_applied(
    model: MelodyModel,
) -> None:
    obj = model.by_uuid(HIERARCHY_UUID)
    diag: context.ContextDiagram = obj.context_diagram

    adiag = diag.render(None, display_port_labels=True)

    for aport in adiag:
        if isinstance(aport, diagram.Box) and aport.port:
            assert aport.floating_labels
