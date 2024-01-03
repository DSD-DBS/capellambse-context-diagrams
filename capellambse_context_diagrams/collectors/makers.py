# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc as cabc

import typing_extensions as te
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
ICON_WIDTH = icon_size + icon_padding * 2
"""Default icon width from capellambse including the padding around it."""
ICON_HEIGHT = icon_size
"""Default icon height from capellambse."""
DEFAULT_LABEL_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "nodeLabels.placement": "INSIDE, V_TOP, H_CENTER"
}
"""Default layout options for a label."""


def make_diagram(diagram: context.ContextDiagram) -> _elkjs.ELKInputData:
    """Return basic skeleton for ``ContextDiagram``s."""
    return {
        "id": diagram.uuid,
        "layoutOptions": _elkjs.get_global_layered_layout_options(),
        "children": [],
        "edges": [],
    }


def make_label(
    text: str,
    icon: tuple[int | float, int | float] = (0, 0),
    layout_options: _elkjs.LayoutOptions | None = None,
) -> _elkjs.ELKInputLabel:
    """Return an
    [`ELKInputLabel`][capellambse_context_diagrams._elkjs.ELKInputLabel].
    """
    label_width, label_height = helpers.get_text_extent(text)
    icon_width, icon_height = icon
    layout_options = layout_options or DEFAULT_LABEL_LAYOUT_OPTIONS
    return {
        "text": text,
        "width": icon_width + label_width + 2 * LABEL_HPAD,
        "height": icon_height + label_height + 2 * LABEL_VPAD,
        "layoutOptions": layout_options,
    }


class _LabelBuilder(te.TypedDict, total=True):
    """Builder object for labels"""

    text: str
    icon: tuple[int | float, int | float]
    layout_options: _elkjs.LayoutOptions


def make_box(
    obj: common.GenericElement,
    *,
    width: int | float = 0,
    height: int | float = 0,
    no_symbol: bool = False,
    slim_width: bool = False,
    label_getter: cabc.Callable[
        [common.GenericElement], cabc.Iterable[_LabelBuilder]
    ] = lambda i: [
        {"text": i.name, "icon": (0, 0), "layout_options": {}}
    ],  # type: ignore
) -> _elkjs.ELKInputChild:
    """Return an
    [`ELKInputChild`][capellambse_context_diagrams._elkjs.ELKInputChild].
    """
    labels = [make_label(**label) for label in label_getter(obj)]
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
        width, height = calculate_height_and_width(
            labels, width=width, height=height, slim_width=slim_width
        )
    return {"id": obj.uuid, "labels": labels, "width": width, "height": height}


def calculate_height_and_width(
    labels: list[_elkjs.ELKInputLabel],
    *,
    width: int | float = 0,
    height: int | float = 0,
    slim_width: bool = False,
) -> tuple[int | float, int | float]:
    """Calculate the size (width and height) from given labels for a box."""
    icon = icon_size + icon_padding * 2
    _height = sum(label["height"] for label in labels) + icon
    min_width = max(label["width"] for label in labels) + icon
    width = min_width if slim_width else max(width, min_width)
    return width, max(height, _height)


def is_symbol(obj: common.GenericElement) -> bool:
    """Check if given `obj` is rendered as a Symbol instead of a Box."""
    return isinstance(obj, BOX_TO_SYMBOL)


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
