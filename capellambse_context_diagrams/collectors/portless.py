# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
Collection of [`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
on diagrams that don't involve ports or any connectors.
"""
from __future__ import annotations

import typing as t
from itertools import chain

from capellambse.model import common, layers

from .. import _elkjs, context
from . import generic, makers

SOURCE_ATTR_NAMES = frozenset(("parent",))
TARGET_ATTR_NAMES = frozenset(("involved", "capability"))


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from exchanges of centric box.

    This is the special context collector for the operational
    architecture layer diagrams (diagrams where elements don't exchange
    via ports/connectors).
    """
    data = generic.collector(diagram)
    centerbox = data["children"][0]
    connections = list(get_exchanges(diagram.target))
    for ex in connections:
        try:
            generic.exchange_data_collector(
                generic.ExchangeData(ex, data, diagram.filters, params),
                collect_exchange_endpoints,
            )
        except AttributeError:
            continue

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    contexts = context_collector(connections, diagram.target)
    made_boxes = {centerbox["id"]: centerbox}
    for i, exchanges, side in contexts:
        var_height = generic.MARKER_PADDING + (
            generic.MARKER_SIZE + generic.MARKER_PADDING
        ) * len(exchanges)
        if not diagram.display_symbols_as_boxes and makers.is_symbol(
            diagram.target
        ):
            height = max(makers.MIN_SYMBOL_HEIGHT, var_height)
        else:
            height = var_height

        if box := made_boxes.get(i.uuid):
            if box is centerbox:
                continue
            box["height"] = height
        else:
            box = makers.make_box(
                i, height=height, no_symbol=diagram.display_symbols_as_boxes
            )
            made_boxes[i.uuid] = box

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del made_boxes[centerbox["id"]]
    data["children"].extend(made_boxes.values())
    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    centerbox["width"] = (
        max(label["width"] for label in centerbox["labels"])
        + 2 * makers.LABEL_HPAD
    )
    if not diagram.display_symbols_as_boxes and makers.is_symbol(
        diagram.target
    ):
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


class ContextInfo(t.NamedTuple):
    """ContextInfo data."""

    element: common.GenericElement
    """An element of context."""
    connections: list[common.GenericElement]
    """The context element's relevant exchanges."""
    side: t.Literal["input", "output"]
    """Whether this is an input or output to the element of interest."""


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
        else:
            obj = source
            side = "input"

        info = ContextInfo(obj, [], side)
        info = ctx.setdefault(obj.uuid, info)
        if exchange not in info.connections:
            info.connections.append(exchange)

    return iter(ctx.values())


def get_exchanges(
    obj: common.GenericElement,
) -> t.Iterator[common.GenericElement]:
    """Yield exchanges safely.

    Yields exchanges from ``.related_exchanges`` or exclusively by
    ``obj`` classtype:
        * Capabilities:
            * ``.extends``,
            * ``.includes``,
            * ``.generalizes`` and their reverse
            * ``.included_by``,
            * ``.extended_by``,
            * ``.generalized_by`` and optionally
            * ``.entity_involvements`` (Operational)
            * ``.component_involvements`` and ``.incoming_exploitations``
              (System)
        * Mission:
            * ``.involvements`` and
            * ``.exploitations``.
    """
    is_op_capability = isinstance(obj, layers.oa.OperationalCapability)
    is_capability = isinstance(obj, layers.ctx.Capability)
    if is_op_capability or is_capability:
        exchanges = [
            obj.includes,
            obj.extends,
            obj.generalizes,
            obj.included_by,
            obj.extended_by,
            obj.generalized_by,
        ]
    elif isinstance(obj, layers.ctx.Mission):
        exchanges = [obj.involvements, obj.exploitations]
    else:
        exchanges = [obj.related_exchanges]

    if is_op_capability:
        exchanges += [obj.entity_involvements]
    elif is_capability:
        exchanges += [obj.component_involvements, obj.incoming_exploitations]

    yield from {i.uuid: i for i in chain.from_iterable(exchanges)}.values()
