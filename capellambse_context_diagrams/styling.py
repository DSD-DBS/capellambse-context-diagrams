# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions for style overrides of diagram elements."""
from __future__ import annotations

import typing as t

from capellambse import diagram
from capellambse.diagram import capstyle
from capellambse.model import common

if t.TYPE_CHECKING:
    from . import serializers

CSSStyles = t.Union[diagram.StyleOverrides, None]
"""
A dictionary with CSS styles. The keys are the attribute names and the
values can be of the types `str`, `aird.RGB` and even
`t.Sequence[aird.RGB]` for coloring a
[`common.GenericElement`][capellambse.model.common.element.GenericElement]
with a gradient.

See also
--------
[parent_is_actor_fills_blue][capellambse_context_diagrams.styling.parent_is_actor_fills_blue]
"""
Styler = t.Callable[
    [common.GenericElement, "serializers.DiagramSerializer"],
    t.Union[diagram.StyleOverrides, None],
]
"""Function that produces `CSSStyles` for given obj."""


def parent_is_actor_fills_blue(
    obj: common.GenericElement, serializer: serializers.DiagramSerializer
) -> CSSStyles:
    """Return ``CSSStyles`` for given ``obj`` rendering it blue."""
    del serializer
    try:
        if obj.owner.is_actor:
            return {
                "fill": [
                    capstyle.COLORS["_CAP_Actor_Blue_min"],
                    capstyle.COLORS["_CAP_Actor_Blue"],
                ],
                "stroke": capstyle.COLORS["_CAP_Actor_Border_Blue"],
            }
    except AttributeError:
        pass

    return None


def style_center_symbol(
    obj: common.GenericElement, serializer: serializers.DiagramSerializer
) -> CSSStyles:
    """Return ``CSSStyles`` for given ``obj``."""
    if obj != serializer._diagram.target:  # type: ignore[has-type]
        return None
    return {
        "fill": capstyle.COLORS["white"],
        "stroke": capstyle.COLORS["gray"],
        "stroke-dasharray": 3,
    }


BLUE_ACTOR_FNCS: dict[str, Styler] = {"node": parent_is_actor_fills_blue}
"""CSSStyle for coloring Actor Functions (Functions of Components with
the attribute `is_actor` set to `True`) with a blue gradient like in
Capella.
"""
SYSTEM_CAP_STYLING: dict[str, Styler] = {"node": style_center_symbol}
"""CSSStyle for custom styling of SystemAnalysis diagrams. The center
box is drawn with a white background and a grey dashed line."""
