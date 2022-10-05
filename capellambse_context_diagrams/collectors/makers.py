# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from capellambse import helpers
from capellambse.model import common, layers
from capellambse.svg.decorations import icon_padding, icon_size

from .. import _elkjs, context

PORT_SIZE = 10
"""Default size of ports in pixels."""
PORT_PADDING = 2
"""Default padding of ports in pixels."""
LABEL_HPAD = 15
"""Horizontal padding left and right of the label."""
LABEL_VPAD = 1
"""Vertical padding above and below the label."""
NEIGHBOR_VMARGIN = 20
"""Vertical space between two neighboring boxes."""
EOI_WIDTH = 150
"""The width of the element of interest."""
MIN_SYMBOL_WIDTH = 30
"""Minimum width of symbols."""
MIN_SYMBOL_HEIGHT = 17
"""Minimum height of symbols."""
MAX_SYMBOL_WIDTH = 150
"""Maximum  width of symbols."""
MAX_SYMBOL_HEIGHT = 135
"""Maximum height of symbols."""
SYMBOL_RATIO = MIN_SYMBOL_WIDTH / MIN_SYMBOL_HEIGHT
"""Width and height ratio of symbols."""
FAULT_PAD = 10
"""Height adjustment for labels."""
BOX_TO_SYMBOL = (
    layers.ctx.Capability,
    layers.oa.OperationalCapability,
    layers.ctx.Mission,
    layers.ctx.SystemComponent,
)
"""
Types that need to be converted to symbols during serialization if
`display_symbols_as_boxes` attribute is `False`.
"""


def make_diagram(diagram: context.ContextDiagram) -> _elkjs.ELKInputData:
    """Return basic skeleton for ``ContextDiagram``s."""
    return {
        "id": diagram.uuid,
        "layoutOptions": _elkjs.get_global_layered_layout_options(),
        "children": [],
        "edges": [],
    }


def make_box(
    obj: common.GenericElement,
    *,
    width: int | float = 0,
    height: int | float = 0,
    no_symbol: bool = False,
) -> _elkjs.ELKInputChild:
    """Return an
    [`ELKInputChild`][capellambse_context_diagrams._elkjs.ELKInputChild].
    """
    labels = [make_label(obj)]
    if not no_symbol and is_symbol(obj):
        if height < MIN_SYMBOL_HEIGHT:
            height = MIN_SYMBOL_HEIGHT
        elif height > MAX_SYMBOL_HEIGHT:
            height = MAX_SYMBOL_HEIGHT
        width = height * SYMBOL_RATIO
        labels[0]["layoutOptions"] = {
            "nodeLabels.placement": "OUTSIDE, V_BOTTOM, H_CENTER"
        }
    else:
        icon = icon_size + icon_padding * 2
        height = max(
            height,
            sum(label["height"] for label in labels) + icon,
        )
        width = max(width, max(label["width"] for label in labels) + icon)

    return {"id": obj.uuid, "labels": labels, "width": width, "height": height}


def is_symbol(obj: common.GenericElement) -> bool:
    """Check if given `obj` is rendered as a Symbol instead of a Box."""
    return isinstance(obj, BOX_TO_SYMBOL)


def make_label(obj: common.GenericElement) -> _elkjs.ELKInputLabel:
    """Return an
    [`ELKInputLabel`][capellambse_context_diagrams._elkjs.ELKInputLabel].
    """
    label_width, label_height = helpers.get_text_extent(obj.name)
    return {
        "text": obj.name,
        "width": label_width + 2 * LABEL_HPAD,
        "height": label_height + 2 * LABEL_VPAD,
        "layoutOptions": {"nodeLabels.placement": "INSIDE, V_TOP, H_CENTER"},
    }


def make_port(uuid: str) -> _elkjs.ELKInputPort:
    """Return an
    [`ELKInputPort`][capellambse_context_diagrams._elkjs.ELKInputPort].
    """
    return {
        "id": uuid,
        "width": 10,
        "height": 10,
        "layoutOptions": {"borderOffset": -8},
    }
