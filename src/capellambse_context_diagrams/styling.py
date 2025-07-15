# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions for style overrides of diagram elements."""

from __future__ import annotations

import dataclasses
import enum
import typing as t

from capellambse import diagram
from capellambse import model as m
from capellambse.diagram import capstyle
from capellambse.extensions import pvmt

from . import helpers

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


class PVMTObjectType(str, enum.Enum):
    """Enumeration of object types for PVMT styling."""

    BOX = "box"
    SYMBOL = "symbol"
    EDGE = "edge"
    LABEL = "label"
    JUNCTION = "junction"


PVMT_COLOR_MAPPINGS: dict[PVMTObjectType, dict[str, str]] = {
    PVMTObjectType.BOX: {
        "__COLOR__": "fill",
        "__BORDER_COLOR__": "stroke",
        "__LABEL_COLOR__": "text_fill",
    },
    PVMTObjectType.EDGE: {
        "__COLOR__": "stroke",
        "__LABEL_COLOR__": "text_fill",
    },
    PVMTObjectType.JUNCTION: {
        "__COLOR__": "stroke",
        "__LABEL_COLOR__": "text_fill",
    },
    PVMTObjectType.SYMBOL: {
        "__COLOR__": "text_fill",
        "__LABEL_COLOR__": "text_fill",
    },
    PVMTObjectType.LABEL: {
        "__COLOR__": "text_fill",
        "__LABEL_COLOR__": "text_fill",
    },
}


@dataclasses.dataclass(frozen=True)
class _PVMTStyling:
    value_groups: list[str]
    children_coloring: bool = False


def normalize_pvmt_styling(
    pvmt_styling: dict[str, t.Any] | list[str] | str | None,
) -> dict[str, t.Any] | None:
    """Normalize ``pvmt_styling`` parameter to dict format.

    Notes
    -----
    The following ways of providing ``pvmt_styling`` are accepted:

    * dict: {"value_groups": [...], "children_coloring": ...}
    * list: ["group1", "group2"]
    * str: "group1"
    * None: None
    """
    if pvmt_styling is None:
        return None

    if isinstance(pvmt_styling, dict):
        if "value_groups" not in pvmt_styling:
            raise ValueError(
                "pvmt_styling dict must contain 'value_groups' key"
            )
        return pvmt_styling

    if isinstance(pvmt_styling, list):
        return {"value_groups": pvmt_styling}

    if isinstance(pvmt_styling, str):
        return {"value_groups": [pvmt_styling]}

    raise TypeError(
        "pvmt_styling must be dict, list, str or None!"
        f" got {type(pvmt_styling)!r}"
    )


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


def _extract_direct_pvmt_styles(
    obj: m.ModelElement,
    pvmt_styling: _PVMTStyling,
    obj_type: PVMTObjectType,
) -> diagram.StyleOverrides:
    """Get PVMT styles directly from the element."""
    color_mappings = PVMT_COLOR_MAPPINGS.get(obj_type, {})
    if not color_mappings:
        return {}

    styleoverrides: diagram.StyleOverrides = {}
    for value_group in pvmt_styling.value_groups:
        try:
            prop_values = obj.pvmt[value_group].property_values
        except (ValueError, pvmt.ScopeError):
            continue

        for pvmt_key, style_key in color_mappings.items():
            try:
                rgb_string = prop_values.by_name(pvmt_key).value
                styleoverrides[style_key] = _parse_rgb_string(rgb_string)
            except KeyError:
                pass

    return styleoverrides


def _parse_rgb_string(rgb_string: str) -> capstyle.RGB:
    """Parse RGB string and return RGB object."""
    return capstyle.RGB.fromcsv(rgb_string.rsplit(",", 1)[0])


def _extract_inherited_pvmt_styles(
    obj: m.ModelElement,
    pvmt_styling: _PVMTStyling,
    obj_type: PVMTObjectType,
) -> diagram.StyleOverrides:
    """Get inherited PVMT styles from parent elements."""
    current: m.ModelElement | None = getattr(obj, "owner", None)
    while current is not None and helpers.has_same_type(obj, current):
        if parent_styles := _extract_direct_pvmt_styles(
            current, pvmt_styling, obj_type
        ):
            return parent_styles

        current = getattr(current, "owner", None)

    return {}


def get_styleoverrides_from_pvmt(
    obj: m.ModelElement,
    pvmt_styling: _PVMTStyling,
    obj_type: PVMTObjectType,
) -> diagram.StyleOverrides:
    """Return PVMT ``StyleOverrides`` for a model element.

    If ``children_coloring`` is enabled and the element has no direct
    PVMT styling, it will inherit styling from the nearest parent
    element that has PVMT styling.
    """
    direct_styles = _extract_direct_pvmt_styles(obj, pvmt_styling, obj_type)
    if direct_styles or not pvmt_styling.children_coloring:
        return direct_styles

    return _extract_inherited_pvmt_styles(obj, pvmt_styling, obj_type)


BLUE_ACTOR_FNCS: dict[str, Styler] = {"node": parent_is_actor_fills_blue}
"""CSSStyle for coloring Actor Functions (Functions of Components with the
attribute `is_actor` set to `True`) with a blue gradient like in Capella."""
SYSTEM_CAP_STYLING: dict[str, Styler] = {"node": style_center_symbol}
"""CSSStyle for custom styling of SystemAnalysis diagrams.

The center box is drawn with a white background and a grey dashed line.
"""
