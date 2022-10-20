# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
Collection of [`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
on diagrams that don't involve ports or any connectors.
"""
from __future__ import annotations

import dataclasses
import typing as t

from capellambse.model import common, layers

from .. import _elkjs, diagram, makers
from . import generic

SOURCE_ATTR_NAMES = frozenset(("parent",))
TARGET_ATTR_NAMES = frozenset(("involved", "capability"))


def collector(
    diag: diagram.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from exchanges of centric box.

    This is the special context collector for the operational
    architecture layer diagrams (diagrams where elements don't exchange
    via ports/connectors).
    """
    data = generic.collector(diag)
    centerbox = data["children"][0]
    connections = list(get_exchanges(diag.target))
    for ex in connections:
        try:
            generic.exchange_data_collector(
                generic.ExchangeData(ex, data, diag.filters, params),
                collect_exchange_endpoints,
            )
        except AttributeError:
            continue

    contexts = context_collector(connections, diag.target)
    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    made_boxes = {centerbox["id"]: centerbox}
    for context in contexts:
        variable_heights = [
            (
                side,
                generic.MARKER_PADDING
                + (generic.MARKER_SIZE + (generic.MARKER_PADDING + 3))
                * len(exchanges),
            )
            for side, exchanges in context.connections.items()
        ]
        side, var_height = max(variable_heights, key=lambda t: t[1])
        if not diag.display_symbols_as_boxes and makers.is_symbol(diag.target):
            height = max(makers.MIN_SYMBOL_HEIGHT, var_height)
        else:
            height = var_height

        if box := made_boxes.get(context.element.uuid):
            if box is centerbox:
                continue
            box["height"] = height
        else:
            box = makers.make_box(
                context.element,
                height=height,
                no_symbol=diag.display_symbols_as_boxes,
            )
            made_boxes[context.element.uuid] = box

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del made_boxes[centerbox["id"]]
    data["children"].extend(made_boxes.values())
    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    centerbox["width"] = (
        max(label["width"] for label in centerbox["labels"])
        + 2 * makers.LABEL_HPAD
    )
    if not diag.display_symbols_as_boxes and makers.is_symbol(diag.target):
        data["layoutOptions"]["spacing.labelNode"] = 5.0
        centerbox["width"] = centerbox["height"] * makers.SYMBOL_RATIO
    return data


def collect_exchange_endpoints(
    e: common.GenericElement,
) -> tuple[common.GenericElement, common.GenericElement]:
    """Safely collect exchange endpoints from `e`."""

    def _get(
        e: common.GenericElement, attrs: t.FrozenSet[str]
    ) -> common.GenericElement:
        for attr in attrs:
            try:
                obj = getattr(e, attr)
                assert isinstance(obj, common.GenericElement)
                return obj
            except AttributeError:
                continue
        raise AttributeError()

    try:
        return _get(e, SOURCE_ATTR_NAMES), _get(e, TARGET_ATTR_NAMES)
    except AttributeError:
        pass
    return generic.collect_exchange_endpoints(e)


@dataclasses.dataclass
class ContextInfo:
    """ContextInfo data."""

    element: common.GenericElement
    """An element of context."""
    connections: dict[
        t.Literal["input", "output"], list[common.GenericElement]
    ]
    """The context element's relevant exchanges, keyed by direction."""

    def __hash__(self) -> int:
        return hash(self.element)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, ContextInfo):
            return False

        eq_elements = self.element == __o.element
        eq_connections = all(
            set(self.connections[side]) == set(__o.connections[side])  # type: ignore[index]
            for side in ("input", "output")
        )
        if eq_elements and eq_connections:
            return True
        return False


def context_collector(
    exchanges: t.Iterable[common.GenericElement],
    obj_oi: common.GenericElement,
) -> t.Iterator[ContextInfo]:
    ctx: dict[str, ContextInfo] = {}
    side: t.Literal["input", "output"]
    for exchange in exchanges:
        try:
            source, target = collect_exchange_endpoints(exchange)
        except AttributeError:
            continue

        if source == obj_oi:
            obj = target
            side = "output"
        elif target == obj_oi:
            obj = source
            side = "input"
        else:
            continue

        info = ContextInfo(
            element=obj, connections={"output": [], "input": []}
        )
        info = ctx.setdefault(obj.uuid, info)
        if exchange not in info.connections[side]:
            info.connections[side].append(exchange)

    return iter(ctx.values())


def get_exchanges(
    obj: common.GenericElement,
) -> t.Iterator[common.GenericElement]:
    """Yield exchanges safely.

    Yields exchanges from `.related_exchanges` or `.extends`,
    `.includes` and `.inheritance` (exclusively for Capabilities).
    """
    is_op_capability = isinstance(obj, layers.oa.OperationalCapability)
    is_capability = isinstance(obj, layers.ctx.Capability)
    if is_op_capability or is_capability:
        exchanges = obj.includes + obj.extends + obj.generalizes
    elif isinstance(obj, layers.ctx.Mission):
        exchanges = obj.involvements + obj.exploitations
    else:
        exchanges = obj.related_exchanges

    if is_op_capability:
        exchanges += obj.entity_involvements
    elif is_capability:
        exchanges += obj.component_involvements + obj.incoming_exploitations

    yield from exchanges
