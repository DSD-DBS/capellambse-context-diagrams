# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions for style overrides of diagram elements."""
from __future__ import annotations

import typing as t

from capellambse import aird
from capellambse.model import common

CSSStyles = t.Union[aird.diagram._StyleOverrides, None]
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
    [common.GenericElement], t.Union[aird.diagram._StyleOverrides, None]
]
"""Function that produces `CSSStyles` for given obj."""


def parent_is_actor_fills_blue(obj: common.GenericElement) -> CSSStyles:
    """
    Returns `CSSStyles` for given obj (i.e. `common.GenericElement`).
    """
    try:
        if obj.owner.is_actor:
            return {
                "fill": [
                    aird.capstyle.COLORS["_CAP_Actor_Blue_min"],
                    aird.capstyle.COLORS["_CAP_Actor_Blue"],
                ],
                "stroke": aird.capstyle.COLORS["_CAP_Actor_Border_Blue"],
            }
    except AttributeError:
        pass

    return None


BLUE_ACTOR_FNCS: dict[str, Styler] = {"node": parent_is_actor_fills_blue}
"""
CSSStyle for coloring Actor Functions (Functions of Components with
the attribute `is_actor` set to `True`) with a blue gradient like in
Capella.
"""
