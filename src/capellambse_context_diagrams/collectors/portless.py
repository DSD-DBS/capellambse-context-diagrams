# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for portless ContextDiagrams.

This collector is used to collect
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that don't involve ports or any connectors.
"""

from __future__ import annotations

import collections.abc as cabc
import typing as t
from itertools import chain

import capellambse.model as m
from capellambse.metamodel import oa, sa

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
    data = generic.collector(diagram, no_symbol=True)
    centerbox = data.children[0]
    connections = list(get_exchanges(diagram.target))
    for ex in connections:
        try:
            generic.exchange_data_collector(
                generic.ExchangeData(ex, data, diagram.filters, params),
                collect_exchange_endpoints,
            )
        except AttributeError:
            continue

    contexts = context_collector(connections, diagram.target)
    global_boxes = {centerbox.id: centerbox}
    made_boxes = {centerbox.id: centerbox}
    if diagram._display_parent_relation and diagram.target.owner is not None:
        box = makers.make_box(
            diagram.target.owner,
            no_symbol=diagram._display_symbols_as_boxes,
            layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
        )
        box.children = [centerbox]
        del data.children[0]
        global_boxes[diagram.target.owner.uuid] = box
        made_boxes[diagram.target.owner.uuid] = box

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    for i, exchanges, side in contexts:
        var_height = generic.MARKER_PADDING + (
            generic.MARKER_SIZE + generic.MARKER_PADDING
        ) * len(exchanges)
        if not diagram._display_symbols_as_boxes and makers.is_symbol(
            diagram.target
        ):
            height = makers.MIN_SYMBOL_HEIGHT + var_height
        else:
            height = var_height

        if box := global_boxes.get(i.uuid):  # type: ignore[assignment]
            if box is centerbox:
                continue
            box.height = height
        else:
            box = makers.make_box(
                i,
                height=height,
                no_symbol=diagram._display_symbols_as_boxes,
            )
            global_boxes[i.uuid] = box
            made_boxes[i.uuid] = box

        if diagram._display_parent_relation and i.owner is not None:
            if not (parent_box := global_boxes.get(i.owner.uuid)):
                parent_box = makers.make_box(
                    i.owner,
                    no_symbol=diagram._display_symbols_as_boxes,
                )
                global_boxes[i.owner.uuid] = parent_box
                made_boxes[i.owner.uuid] = parent_box

            parent_box.children.append(global_boxes.pop(i.uuid))
            for label in parent_box.labels:
                label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del global_boxes[centerbox.id]
    data.children.extend(global_boxes.values())

    if diagram._display_parent_relation:
        owner_boxes: dict[str, _elkjs.ELKInputChild] = {
            uuid: box for uuid, box in made_boxes.items() if box.children
        }
        generic.move_parent_boxes_to_owner(owner_boxes, diagram.target, data)
        generic.move_edges(owner_boxes, connections, data)

    centerbox.height = max(centerbox.height, *stack_heights.values())
    if not diagram._display_symbols_as_boxes and makers.is_symbol(
        diagram.target
    ):
        data.layoutOptions["spacing.labelNode"] = 5.0
    return data


def collect_exchange_endpoints(
    e: m.ModelElement,
) -> tuple[m.ModelElement, m.ModelElement]:
    """Safely collect exchange endpoints from `e`."""

    def _get(e: m.ModelElement, attrs: frozenset[str]) -> m.ModelElement:
        for attr in attrs:
            try:
                obj = getattr(e, attr)
                assert isinstance(obj, m.ModelElement)
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

    element: m.ModelElement
    """An element of context."""
    connections: list[m.ModelElement]
    """The context element's relevant exchanges."""
    side: t.Literal["input", "output"]
    """Whether this is an input or output to the element of interest."""


def context_collector(
    exchanges: t.Iterable[m.ModelElement],
    obj_oi: m.ModelElement,
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
    obj: m.ModelElement,
    filter: cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ] = lambda i: i,
) -> t.Iterator[t.Any]:
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
    is_op_capability = isinstance(obj, oa.OperationalCapability)
    is_capability = isinstance(obj, sa.Capability)
    if is_op_capability or is_capability:
        exchanges = [
            obj.includes,
            obj.extends,
            obj.generalizes,
            obj.included_by,
            obj.extended_by,
            obj.generalized_by,
        ]
    elif isinstance(obj, sa.Mission):
        exchanges = [obj.involvements, obj.exploitations]
    else:
        exchanges = [obj.related_exchanges]

    if is_op_capability:
        exchanges += [obj.entity_involvements]
    elif is_capability:
        exchanges += [obj.component_involvements, obj.incoming_exploitations]

    filtered = filter(chain.from_iterable(exchanges))
    yield from {i.uuid: i for i in filtered}.values()
