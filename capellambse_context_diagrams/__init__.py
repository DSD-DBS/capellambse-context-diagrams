# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
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

import collections.abc as cabc
import logging
import typing as t
from importlib import metadata

from capellambse.aird import COLORS, CSSdef, capstyle
from capellambse.model import common
from capellambse.model.crosslayer import fa
from capellambse.model.layers import ctx, la, oa, pa
from capellambse.model.modeltypes import DiagramType

from . import context

try:
    __version__ = metadata.version("capellambse-context-diagrams")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"
del metadata

ClassPair = tuple[type[common.GenericElement], DiagramType]

logger = logging.getLogger(__name__)

ATTR_NAME = "context_diagram"


def init() -> None:
    """Initialize the extension."""
    register_classes()
    register_interface_context()
    # register_functional_context() XXX: Future


def register_classes() -> None:
    """Add the `context_diagram` property to the relevant model objects."""
    supported_classes: list[ClassPair] = [
        (oa.Entity, DiagramType.OAB),
        (oa.OperationalActivity, DiagramType.OAIB),
        (oa.OperationalCapability, DiagramType.OCB),
        (ctx.Mission, DiagramType.MCB),
        (ctx.Capability, DiagramType.MCB),
        (ctx.SystemComponent, DiagramType.SAB),
        (ctx.SystemFunction, DiagramType.SDFB),
        (la.LogicalComponent, DiagramType.LAB),
        (la.LogicalFunction, DiagramType.LDFB),
        (pa.PhysicalComponent, DiagramType.PAB),
        (pa.PhysicalFunction, DiagramType.PDFB),
    ]
    patch_styles(supported_classes)
    class_: type[common.GenericElement]
    for class_, dgcls in supported_classes:
        common.set_accessor(
            class_, ATTR_NAME, context.ContextAccessor(dgcls.value)
        )


def patch_styles(classes: cabc.Iterable[ClassPair]) -> None:
    """Add missing default styling to default styles.

    See Also
    --------
    [capstyle.get_style][capellambse.aird.capstyle.get_style] : Default
        style getter.
    """
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
    circle_style = {"fill": COLORS["_CAP_xAB_Function_Border_Green"]}
    for _, dt in classes:
        capstyle.STYLES[dt.value]["Circle.FunctionalExchange"] = circle_style


def register_interface_context() -> None:
    """Add the `context_diagram` property to interface model objects."""
    common.set_accessor(
        oa.CommunicationMean,
        ATTR_NAME,
        context.InterfaceContextAccessor(
            {
                oa.EntityPkg: DiagramType.OAB.value,
                oa.Entity: DiagramType.OAB.value,
            }
        ),
    )
    common.set_accessor(
        fa.ComponentExchange,
        ATTR_NAME,
        context.InterfaceContextAccessor(
            {
                ctx.SystemComponentPkg: DiagramType.SAB.value,
                ctx.SystemComponent: DiagramType.SAB.value,
                la.LogicalComponentPkg: DiagramType.LAB.value,
                la.LogicalComponent: DiagramType.LAB.value,
                pa.PhysicalComponentPkg: DiagramType.PAB.value,
                pa.PhysicalComponent: DiagramType.PAB.value,
            },
        ),
    )


def register_functional_context() -> None:
    """Add the `functional_context_diagram` attribute to `ModelObject`s.

    !!! bug "Full of bugs"

        The functional context diagrams will be available soon.
    """
    attr_name = f"functional_{ATTR_NAME}"
    supported_classes: list[
        tuple[type[common.GenericElement], DiagramType]
    ] = [
        (oa.Entity, DiagramType.OAB),
        (ctx.SystemComponent, DiagramType.SAB),
        (la.LogicalComponent, DiagramType.LAB),
        (pa.PhysicalComponent, DiagramType.PAB),
    ]
    class_: type[common.GenericElement]
    for class_, dgcls in supported_classes:
        common.set_accessor(
            class_,
            attr_name,
            context.FunctionalContextAccessor(dgcls.value),
        )
