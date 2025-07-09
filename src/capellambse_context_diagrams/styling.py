# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions for style overrides of diagram elements."""

from __future__ import annotations

import dataclasses
import typing as t

from capellambse import diagram
from capellambse import model as m
from capellambse.diagram import capstyle
from capellambse.extensions import pvmt

if t.TYPE_CHECKING:
    from . import serializers

CSSStyles = diagram.StyleOverrides | None
"""A dictionary with CSS styles. The keys are the attribute names and the
values can be of the types `str`, `aird.RGB` and even `t.Sequence[aird.RGB]`
for coloring a [`ModelElement`][capellambse.model.ModelElement] with a
gradient.

See also
--------
[parent_is_actor_fills_blue][capellambse_context_diagrams.styling.parent_is_actor_fills_blue]
"""
Styler = t.Callable[
    [m.ModelElement, "serializers.DiagramSerializer"],
    diagram.StyleOverrides | None,
]
"""Function that produces `CSSStyles` for given obj."""


@dataclasses.dataclass(frozen=True)
class _PVMTStyling:
    value_groups: list[str]
    children_coloring: bool = False


def parent_is_actor_fills_blue(
    obj: m.ModelElement, serializer: serializers.DiagramSerializer
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
    obj: m.ModelElement, serializer: serializers.DiagramSerializer
) -> CSSStyles:
    """Return ``CSSStyles`` for given ``obj``."""
    if obj != serializer._diagram.target:
        return None
    return {
        "fill": capstyle.COLORS["white"],
        "stroke": capstyle.COLORS["gray"],
        "stroke-dasharray": "3",
    }


def _get_direct_pvmt_styles(
    obj: m.ModelElement, pvmt_styling: _PVMTStyling
) -> diagram.StyleOverrides:
    """Get PVMT styles directly from the element."""
    styleoverrides: diagram.StyleOverrides = {}
    color_mappings: dict[str, str] = {
        "__COLOR__": "fill",
        "__BORDER_COLOR__": "stroke",
        "__LABEL_COLOR__": "text_fill",
    }
    for value_group in pvmt_styling.value_groups:
        try:
            prop_values = obj.pvmt[value_group].property_values
        except (ValueError, pvmt.ScopeError):
            continue

        for pvmt_key, style_key in color_mappings.items():
            try:
                rgb_string = prop_values.by_name(pvmt_key).value
                styleoverrides[style_key] = capstyle.RGB.fromcsv(
                    rgb_string.rsplit(",", 1)[0]
                )
            except KeyError:
                pass

    return styleoverrides


def _get_inherited_pvmt_styles(
    obj: m.ModelElement, pvmt_styling: _PVMTStyling
) -> diagram.StyleOverrides:
    """Get inherited PVMT styles from parent elements."""
    current: m.ModelElement | None = getattr(obj, "owner", None)
    type_name = type(obj).__name__
    while current is not None and type_name == type(current).__name__:
        if parent_styles := _get_direct_pvmt_styles(current, pvmt_styling):
            return parent_styles

        current = getattr(current, "owner", None)

    return {}


def get_styleoverrides_from_pvmt(
    obj: m.ModelElement, pvmt_styling: _PVMTStyling
) -> diagram.StyleOverrides:
    """Return PVMT ``StyleOverrides`` for a model element.

    If ``children_coloring`` is enabled and the element has no direct
    PVMT styling, it will inherit styling from the nearest parent
    element that has PVMT styling.
    """
    direct_styles = _get_direct_pvmt_styles(obj, pvmt_styling)
    if direct_styles or not pvmt_styling.children_coloring:
        return direct_styles

    return _get_inherited_pvmt_styles(obj, pvmt_styling)


BLUE_ACTOR_FNCS: dict[str, Styler] = {"node": parent_is_actor_fills_blue}
"""CSSStyle for coloring Actor Functions (Functions of Components with the
attribute `is_actor` set to `True`) with a blue gradient like in Capella."""
SYSTEM_CAP_STYLING: dict[str, Styler] = {"node": style_center_symbol}
"""CSSStyle for custom styling of SystemAnalysis diagrams.

The center box is drawn with a white background and a grey dashed line.
"""
