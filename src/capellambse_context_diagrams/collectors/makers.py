# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc as cabc

import capellambse.model as m
import typing_extensions as te
from capellambse import helpers as chelpers
from capellambse.metamodel import oa, sa
from capellambse.svg import helpers as svghelpers
from capellambse.svg.decorations import icon_padding, icon_size

from .. import _elkjs, context

PORT_SIZE = 10
"""Default size of ports in pixels."""
PORT_PADDING = 2
"""Default padding of ports in pixels."""
LABEL_HPAD = 3
"""Horizontal padding left and right of the label."""
LABEL_VPAD = 1
"""Vertical padding above and below the label."""
MAX_LABEL_WIDTH = 200
"""Maximum width for edge labels."""
NEIGHBOR_VMARGIN = 20
"""Vertical space between two neighboring boxes."""
EOI_WIDTH = 100
"""The width of the element of interest."""
MAX_BOX_WIDTH = 150
"""Maximum width of boxes."""
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
    sa.Capability.__name__,
    oa.OperationalCapability.__name__,
    sa.Mission.__name__,
    sa.SystemComponent.__name__,
    "SystemHumanActor",
    "SystemActor",
)
"""Types that need to be converted to symbols during serialization if
`display_symbols_as_boxes` attribute is `False`."""
ICON_WIDTH = icon_size + icon_padding * 2
"""Default icon width from capellambse including the padding around it."""
ICON_HEIGHT = icon_size
"""Default icon height from capellambse."""
DEFAULT_LABEL_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "nodeLabels.placement": "INSIDE, V_TOP, H_CENTER"
}
"""Default layout options for a label."""
CENTRIC_LABEL_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "nodeLabels.placement": "INSIDE, V_CENTER, H_CENTER"
}
"""Layout options for a centric label."""
SYMBOL_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "nodeLabels.placement": "OUTSIDE, V_BOTTOM, H_CENTER"
}
"""Layout options for a symbol label."""

STYLECLASS_PREFIX = "__Derived"


def make_diagram(diagram: context.ContextDiagram) -> _elkjs.ELKInputData:
    """Return basic skeleton for ``ContextDiagram``s."""
    return _elkjs.ELKInputData(
        id=diagram.uuid,
        layoutOptions=_elkjs.get_global_layered_layout_options(),
        children=[],
        edges=[],
    )


def make_label(
    text: str,
    icon: tuple[int | float, int | float] = (ICON_WIDTH, ICON_HEIGHT),
    layout_options: _elkjs.LayoutOptions | None = None,
    max_width: int | float | None = None,
) -> list[_elkjs.ELKInputLabel]:
    """Return a label.

    See Also
    --------
    [`ELKInputLabel`][capellambse_context_diagrams._elkjs.ELKInputLabel] :
        Input data for an ELK label.
    """
    label_width, label_height = chelpers.get_text_extent(text)
    icon_width, _ = icon
    lines: cabc.Sequence[str] = [text]
    if max_width is not None and label_width > max_width:
        lines, _, _ = svghelpers.check_for_horizontal_overflow(
            text,
            max_width,
            icon_padding,
            icon_width,
        )

    layout_options = layout_options or CENTRIC_LABEL_LAYOUT_OPTIONS
    labels: list[_elkjs.ELKInputLabel] = []
    for line in lines:
        label_width, label_height = chelpers.get_text_extent(line)
        labels.append(
            _elkjs.ELKInputLabel(
                text=line,
                width=(
                    (icon_width + label_width + 2 * LABEL_HPAD) if line else 0
                ),
                height=(label_height + 2 * LABEL_VPAD) if line else 0,
                layoutOptions=layout_options,
            )
        )
    return labels


class _LabelBuilder(te.TypedDict, total=True):
    """Builder object for labels."""

    text: str
    icon: tuple[int | float, int | float]
    layout_options: _elkjs.LayoutOptions


def make_box(
    obj: m.ModelElement,
    *,
    width: int | float = 0,
    height: int | float = 0,
    no_symbol: bool = False,
    slim_width: bool = True,
    label_getter: cabc.Callable[
        [m.ModelElement], cabc.Iterable[_LabelBuilder]
    ] = lambda i: [
        {
            "text": i.name,
            "icon": (ICON_WIDTH, 0),
            "layout_options": {},
        }
    ],
    max_label_width: int | float = MAX_BOX_WIDTH,
    layout_options: _elkjs.LayoutOptions | None = None,
) -> _elkjs.ELKInputChild:
    """Return a box.

    See Also
    --------
    [`ELKInputChild`][capellambse_context_diagrams._elkjs.ELKInputChild] :
        Input data for an ELK box.
    """
    layout_options = layout_options or CENTRIC_LABEL_LAYOUT_OPTIONS
    if symbol := not no_symbol and is_symbol(obj):
        max_label_width = 200

    labels: list[_elkjs.ELKInputLabel] = []
    for label_builder in label_getter(obj):
        if not label_builder.get("layout_options"):
            label_builder.setdefault("layout_options", {}).update(
                layout_options
            )

        labels.extend(make_label(**label_builder, max_width=max_label_width))

    if symbol:
        if height < MIN_SYMBOL_HEIGHT:
            height = MIN_SYMBOL_HEIGHT
        elif height > MAX_SYMBOL_HEIGHT:
            height = MAX_SYMBOL_HEIGHT
        width = height * SYMBOL_RATIO
        for label in labels:
            label.layoutOptions.update(SYMBOL_LAYOUT_OPTIONS)
    else:
        width, height = calculate_height_and_width(
            labels, width=width, height=height, slim_width=slim_width
        )
    return _elkjs.ELKInputChild(
        id=obj.uuid,
        labels=labels,
        width=width,
        height=height,
    )


def calculate_height_and_width(
    labels: list[_elkjs.ELKInputLabel],
    *,
    width: int | float = 0,
    height: int | float = 0,
    slim_width: bool = False,
) -> tuple[int | float, int | float]:
    """Calculate the size (width and height) from given labels for a box."""
    icon = icon_size + icon_padding * 2
    _height = sum(label.height + 2 * LABEL_VPAD for label in labels) + icon
    min_width = max(label.width + 2 * LABEL_HPAD for label in labels)
    width = min_width if slim_width else max(width, min_width)
    return width, max(height, _height)


def is_symbol(obj: str | m.ModelElement | None) -> bool:
    """Check if given `obj` is rendered as a Symbol instead of a Box."""
    if obj is None:
        return False
    if isinstance(obj, str):
        return obj in BOX_TO_SYMBOL
    return type(obj).__name__ in BOX_TO_SYMBOL


def make_port(uuid: str) -> _elkjs.ELKInputPort:
    """Return a port.

    See Also
    --------
    [`ELKInputPort`][capellambse_context_diagrams._elkjs.ELKInputPort] :
        Input data for an ELK port.
    """
    return _elkjs.ELKInputPort(
        id=uuid,
        width=PORT_SIZE,
        height=PORT_SIZE,
        layoutOptions={"borderOffset": -4 * PORT_PADDING},
    )
