# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Class register for all ContextCiagrams for capellambse."""

from __future__ import annotations

import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa, la, oa, pa, sa
from capellambse.model import DiagramType

from . import enums, styling

DefaultRenderParams = dict[str, t.Any]
SupportedContextClass = tuple[
    type[m.ModelElement], DiagramType, DefaultRenderParams
]
SupportedInterfaceContextClass = tuple[
    type[m.ModelElement], dict[type[m.ModelElement], str], DefaultRenderParams
]

CONTEXT_DIAGRAM_CLASSES: list[SupportedContextClass] = [
    (oa.Entity, DiagramType.OAB, {}),
    (
        oa.OperationalActivity,
        DiagramType.OAB,
        {"display_parent_relation": True},
    ),
    (oa.OperationalCapability, DiagramType.OCB, {}),
    (sa.Mission, DiagramType.MCB, {}),
    (
        sa.Capability,
        DiagramType.MCB,
        {"display_symbols_as_boxes": False},
    ),
    (
        sa.SystemComponent,
        DiagramType.SAB,
        {
            "display_symbols_as_boxes": True,
            "display_parent_relation": True,
            "display_derived_interfaces": True,
            "include_external_context": True,
            "render_styles": styling.BLUE_ACTOR_FNCS,
        },
    ),
    (
        sa.SystemFunction,
        DiagramType.SAB,
        {
            "display_symbols_as_boxes": True,
            "display_parent_relation": True,
            "render_styles": styling.BLUE_ACTOR_FNCS,
        },
    ),
    (
        la.LogicalComponent,
        DiagramType.LAB,
        {
            "display_symbols_as_boxes": True,
            "display_parent_relation": True,
            "include_external_context": True,
            "display_derived_interfaces": True,
            "render_styles": styling.BLUE_ACTOR_FNCS,
        },
    ),
    (
        la.LogicalFunction,
        DiagramType.LAB,
        {
            "display_symbols_as_boxes": True,
            "display_parent_relation": True,
            "render_styles": styling.BLUE_ACTOR_FNCS,
        },
    ),
    (
        pa.PhysicalComponent,
        DiagramType.PAB,
        {
            "display_parent_relation": True,
            "display_port_labels": True,
            "display_derived_interfaces": True,
            "include_external_context": True,
            "hide_context_owner": True,
            "edge_direction": enums.EDGE_DIRECTION.RIGHT,
        },
    ),
    (
        pa.PhysicalFunction,
        DiagramType.PAB,
        {
            "display_parent_relation": True,
        },
    ),
]
INTERFACE_CONTEXT_CLASSES: list[SupportedInterfaceContextClass] = [
    (
        oa.CommunicationMean,
        {
            oa.EntityPkg: DiagramType.OAB.value,
            oa.Entity: DiagramType.OAB.value,
        },
        {"include_interface": True},
    ),
    (
        fa.ComponentExchange,
        {
            sa.SystemComponentPkg: DiagramType.SAB.value,
            sa.SystemComponent: DiagramType.SAB.value,
            la.LogicalComponentPkg: DiagramType.LAB.value,
            la.LogicalComponent: DiagramType.LAB.value,
            pa.PhysicalComponentPkg: DiagramType.PAB.value,
            pa.PhysicalComponent: DiagramType.PAB.value,
        },
        {"include_interface": True, "include_port_allocations": True},
    ),
    (
        cs.PhysicalLink,
        {
            sa.SystemComponentPkg: DiagramType.SAB.value,
            sa.SystemComponent: DiagramType.SAB.value,
            la.LogicalComponentPkg: DiagramType.LAB.value,
            la.LogicalComponent: DiagramType.LAB.value,
            pa.PhysicalComponentPkg: DiagramType.PAB.value,
            pa.PhysicalComponent: DiagramType.PAB.value,
        },
        {"include_interface": True, "display_port_labels": True},
    ),
]
REALIZATION_VIEW_CLASSES: list[SupportedContextClass] = [
    (oa.Entity, DiagramType.OAB, {}),
    (oa.OperationalActivity, DiagramType.OAIB, {}),
    (sa.SystemComponent, DiagramType.SAB, {}),
    (sa.SystemFunction, DiagramType.SDFB, {}),
    (la.LogicalComponent, DiagramType.LAB, {}),
    (la.LogicalFunction, DiagramType.LDFB, {}),
    (pa.PhysicalComponent, DiagramType.PAB, {}),
    (pa.PhysicalFunction, DiagramType.PDFB, {}),
]
DATAFLOW_CLASSES: list[SupportedContextClass] = [
    (oa.OperationalCapability, DiagramType.OAIB, {}),  # portless
    (sa.Capability, DiagramType.SDFB, {}),  # default
]
