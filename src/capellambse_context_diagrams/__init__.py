# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
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
import shutil
from importlib import metadata

import capellambse.model as m
from capellambse.diagram import COLORS, CSSdef, capstyle
from capellambse.metamodel import cs, information
from capellambse.model import DiagramType

from . import _elkjs, _registry, context

try:
    __version__ = metadata.version("capellambse-context-diagrams")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"

logger = logging.getLogger(__name__)

ATTR_NAME = "context_diagram"


def install_elk() -> None:
    """Install an ELK.js binary.

    When rendering a context diagram, elk.js will be installed
    automatically into a persistent local cache directory. This function
    may be called while building a container, starting a server or
    similar tasks in order to prepare the elk.js execution environment
    ahead of time.
    """
    if shutil.which("deno") and "dev" in metadata.version(
        "capellambse_context_diagrams"
    ):
        return

    _elkjs.elk_manager.spawn_process()


def init() -> None:
    """Initialize the extension."""
    register_classes()
    register_interface_context()
    register_physical_port_context()
    register_tree_view()
    register_realization_view()
    register_data_flow_view()
    register_cable_tree_view()


def register_classes() -> None:
    """Add the `context_diagram` property to the relevant model objects."""
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
    for (
        class_,
        dgcls,
        default_render_params,
    ) in _registry.CONTEXT_DIAGRAM_CLASSES:
        accessor = context.ContextAccessor(dgcls.value, default_render_params)
        m.set_accessor(class_, ATTR_NAME, accessor)
        capstyle.STYLES[dgcls.value]["Circle.FunctionalExchange"] = (
            circle_style
        )


def register_interface_context() -> None:
    """Add the `context_diagram` property to interface model objects."""
    class_: type[m.ModelElement]
    for (
        class_,
        dgclasses,
        default_render_params,
    ) in _registry.INTERFACE_CONTEXT_CLASSES:
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
    styles: dict[str, dict[str, capstyle.CSSdef]] = {}
    for class_, dgcls, _ in _registry.REALIZATION_VIEW_CLASSES:
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
    """Add the `data_flow_view` attribute to ``Capability``s."""
    class_: type[m.ModelElement]
    for class_, dgcls, default_render_params in _registry.DATAFLOW_CLASSES:
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
