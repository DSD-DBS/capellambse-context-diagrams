# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""The Context Diagrams model extension.

This extension adds a new property to many model elements called
`context_diagram`, which allows access automatically generated diagrams
of an element's "context".

The context of an element is defined as the collection of the element
itself, its ports, the exchanges that flow into or out of the ports, as
well as the ports on the other side of the exchange and the ports'
direct parent elements.

The element of interest uses the regular styling (configurable via
function), other elements use a white background color to distinguish
them.
"""

from __future__ import annotations

import logging
import typing as t
from importlib import metadata

import capellambse.model as m
from capellambse.diagram import COLORS, CSSdef, capstyle
from capellambse.metamodel import cs, fa, information, la, oa, pa, sa
from capellambse.model import DiagramType

from . import _elkjs, context, styling

try:
    __version__ = metadata.version("capellambse-context-diagrams")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"
del metadata

DefaultRenderParams = dict[str, t.Any]
SupportedContextClass = tuple[
    type[m.ModelElement], DiagramType, DefaultRenderParams
]
SupportedInterfaceContextClass = tuple[
    type[m.ModelElement], dict[type[m.ModelElement], str], DefaultRenderParams
]
logger = logging.getLogger(__name__)

ATTR_NAME = "context_diagram"


def install_elk() -> None:
    """Install elk.js and its dependencies into the local cache directory.

    When rendering a context diagram, elk.js will be installed
    automatically into a persistent local cache directory. This function
    may be called while building a container, starting a server or
    similar tasks in order to prepare the elk.js execution environment
    ahead of time.
    """
    _elkjs._install_required_npm_pkg_versions()


def init() -> None:
    """Initialize the extension."""
    register_classes()
    register_interface_context()
    register_physical_port_context()
    register_tree_view()
    register_realization_view()
    register_data_flow_view()
    register_cable_tree_view()
    register_custom_diagram()
    # register_functional_context() XXX: Future


def register_classes() -> None:
    """Add the `context_diagram` property to the relevant model objects."""
    supported_classes: list[SupportedContextClass] = [
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
    cap: dict[str, CSSdef] = {
        "fill": [COLORS["_CAP_Entity_Gray_min"], COLORS["_CAP_Entity_Gray"]],
        "stroke": COLORS["dark_gray"],
        "text_fill": COLORS["black"],
    }
    capstyle.STYLES["Missions Capabilities Blank"].update(
        {"Box.Capability": cap, "Box.Mission": cap}
    )
    capstyle.STYLES["Operational Capabilities Blank"][
        "Box.OperationalCapability"
    ] = cap
    circle_style: dict[str, CSSdef] = {
        "fill": COLORS["_CAP_xAB_Function_Border_Green"],
    }
    class_: type[m.ModelElement]
    for class_, dgcls, default_render_params in supported_classes:
        accessor = context.ContextAccessor(dgcls.value, default_render_params)
        m.set_accessor(class_, ATTR_NAME, accessor)
        capstyle.STYLES[dgcls.value]["Circle.FunctionalExchange"] = (
            circle_style
        )


def register_interface_context() -> None:
    """Add the `context_diagram` property to interface model objects."""
    supported_classes: list[SupportedInterfaceContextClass] = [
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
    class_: type[m.ModelElement]
    for class_, dgclasses, default_render_params in supported_classes:
        accessor = context.InterfaceContextAccessor(
            dgclasses, default_render_params
        )
        m.set_accessor(class_, ATTR_NAME, accessor)

    port_alloc_output_style: dict[str, CSSdef] = {
        "fill": COLORS["_CAP_xAB_Function_Border_Green"],
        "stroke": COLORS["_CAP_xAB_Function_Border_Green"],
        "stroke-dasharray": "2",
        "text_fill": COLORS["black"],
    }
    port_alloc_input_style: dict[str, CSSdef] = {
        "fill": COLORS["dark_orange"],
        "stroke": COLORS["dark_orange"],
        "stroke-dasharray": "2",
        "text_fill": COLORS["black"],
    }
    for dt in (DiagramType.SAB, DiagramType.LAB, DiagramType.PAB):
        capstyle.STYLES[dt.value]["Edge.PortInputAllocation"] = (
            port_alloc_input_style
        )
        capstyle.STYLES[dt.value]["Edge.PortOutputAllocation"] = (
            port_alloc_output_style
        )


def register_functional_context() -> None:
    """Add the `functional_context_diagram` attribute to `ModelObject`s.

    !!! bug "Full of bugs"

    The functional context diagrams will be available soon.
    """
    attr_name = f"functional_{ATTR_NAME}"
    supported_classes: list[tuple[type[m.ModelElement], DiagramType]] = [
        (oa.Entity, DiagramType.OAB),
        (sa.SystemComponent, DiagramType.SAB),
        (la.LogicalComponent, DiagramType.LAB),
        (pa.PhysicalComponent, DiagramType.PAB),
    ]
    class_: type[m.ModelElement]
    for class_, dgcls in supported_classes:
        m.set_accessor(
            class_,
            attr_name,
            context.FunctionalContextAccessor(dgcls.value),
        )


def register_physical_port_context() -> None:
    """Add the `context_diagram` attribute to `PhysicalPort`s."""
    m.set_accessor(
        cs.PhysicalPort,
        ATTR_NAME,
        context.PhysicalPortContextAccessor(DiagramType.PAB.value, {}),
    )


def register_tree_view() -> None:
    """Add the ``tree_view`` attribute to ``Class``es."""
    m.set_accessor(
        information.Class,
        "tree_view",
        context.ClassTreeAccessor(DiagramType.CDB.value),
    )


def register_realization_view() -> None:
    """Add the ``realization_view`` attribute to various objects.

    Adds ``realization_view`` to Activities, Functions and Components
    of all layers.
    """
    supported_classes: list[SupportedContextClass] = [
        (oa.Entity, DiagramType.OAB, {}),
        (oa.OperationalActivity, DiagramType.OAIB, {}),
        (sa.SystemComponent, DiagramType.SAB, {}),
        (sa.SystemFunction, DiagramType.SDFB, {}),
        (la.LogicalComponent, DiagramType.LAB, {}),
        (la.LogicalFunction, DiagramType.LDFB, {}),
        (pa.PhysicalComponent, DiagramType.PAB, {}),
        (pa.PhysicalFunction, DiagramType.PDFB, {}),
    ]
    styles: dict[str, dict[str, capstyle.CSSdef]] = {}
    for class_, dgcls, _ in supported_classes:
        m.set_accessor(
            class_,
            "realization_view",
            context.RealizationViewContextAccessor("RealizationView Diagram"),
        )
        styles.update(capstyle.STYLES.get(dgcls.value, {}))

    capstyle.STYLES["RealizationView Diagram"] = styles
    capstyle.STYLES["RealizationView Diagram"].update(
        capstyle.STYLES["__GLOBAL__"]
    )
    capstyle.STYLES["RealizationView Diagram"]["Edge.Realization"] = {
        "stroke": capstyle.COLORS["dark_gray"],
        "marker-end": "FineArrowMark",
        "stroke-dasharray": "5",
    }


def register_data_flow_view() -> None:
    supported_classes: list[SupportedContextClass] = [
        (oa.OperationalCapability, DiagramType.OAIB, {}),  # portless
        (sa.Capability, DiagramType.SDFB, {}),  # default
    ]
    class_: type[m.ModelElement]
    for class_, dgcls, default_render_params in supported_classes:
        accessor = context.DataFlowAccessor(dgcls.value, default_render_params)
        m.set_accessor(class_, "data_flow_view", accessor)


def register_cable_tree_view() -> None:
    """Add the `cable_tree_view` attribute to `PhysicalLink`s."""
    m.set_accessor(
        cs.PhysicalLink,
        "cable_tree",
        context.CableTreeAccessor(
            DiagramType.PAB.value,
            {},
        ),
    )


def register_custom_diagram() -> None:
    """Add the `custom_diagram` attribute to `ModelObject`s."""
    supported_classes: list[tuple[type[m.ModelElement], DiagramType]] = [
        (oa.Entity, DiagramType.OAB),
        (oa.OperationalActivity, DiagramType.OAB),
        (oa.OperationalCapability, DiagramType.OCB),
        (oa.CommunicationMean, DiagramType.OAB),
        (sa.Mission, DiagramType.MCB),
        (sa.Capability, DiagramType.MCB),
        (sa.SystemComponent, DiagramType.SAB),
        (sa.SystemFunction, DiagramType.SAB),
        (la.LogicalComponent, DiagramType.LAB),
        (la.LogicalFunction, DiagramType.LAB),
        (pa.PhysicalComponent, DiagramType.PAB),
        (pa.PhysicalFunction, DiagramType.PAB),
        (cs.PhysicalLink, DiagramType.PAB),
        (cs.PhysicalPort, DiagramType.PAB),
        (fa.ComponentExchange, DiagramType.SAB),
        (information.Class, DiagramType.CDB),
    ]
    for class_, dgcls in supported_classes:
        m.set_accessor(
            class_,
            "custom_diagram",
            context.CustomContextAccessor(dgcls.value, {}),
        )
