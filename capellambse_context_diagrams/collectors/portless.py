# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
Collection of [`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
on diagrams that don't involve ports or any connectors.
"""
from __future__ import annotations

import collections.abc as cabc
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
    data = generic.collector(diagram, no_symbol=True)
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
    if diagram.display_parent_relation and diagram.target.owner is not None:
        box = makers.make_box(
            diagram.target.owner,
            no_symbol=diagram.display_symbols_as_boxes,
            layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
        )
        box["children"] = [centerbox]
        del data["children"][0]
        made_boxes[diagram.target.owner.uuid] = box

    for i, exchanges, side in contexts:
        var_height = generic.MARKER_PADDING + (
            generic.MARKER_SIZE + generic.MARKER_PADDING
        ) * len(exchanges)
        if not diagram.display_symbols_as_boxes and makers.is_symbol(
            diagram.target
        ):
            height = makers.MIN_SYMBOL_HEIGHT + var_height
        else:
            height = var_height

        if box := made_boxes.get(i.uuid):  # type: ignore[assignment]
            if box is centerbox:
                continue
            box["height"] = height
        else:
            box = makers.make_box(
                i,
                height=height,
                no_symbol=diagram.display_symbols_as_boxes,
            )
            made_boxes[i.uuid] = box

        if diagram.display_parent_relation:
            if i.owner is not None:
                if not (parent_box := made_boxes.get(i.owner.uuid)):
                    parent_box = makers.make_box(
                        i.owner,
                        no_symbol=diagram.display_symbols_as_boxes,
                    )
                    made_boxes[i.owner.uuid] = parent_box

                parent_box.setdefault("children", []).append(
                    made_boxes.pop(i.uuid)
                )
                for label in parent_box["labels"]:
                    label["layoutOptions"] = (
                        makers.DEFAULT_LABEL_LAYOUT_OPTIONS
                    )

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del made_boxes[centerbox["id"]]
    data["children"].extend(made_boxes.values())

    if diagram.display_parent_relation:
        _move_parent_boxes(diagram.target, data)
        _move_edges(made_boxes, connections, data)

    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    if not diagram.display_symbols_as_boxes and makers.is_symbol(
        diagram.target
    ):
        data["layoutOptions"]["spacing.labelNode"] = 5.0
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
    filter: cabc.Callable[
        [cabc.Iterable[common.GenericElement]],
        cabc.Iterable[common.GenericElement],
    ] = lambda i: i,
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

    filtered = filter(chain.from_iterable(exchanges))
    yield from {i.uuid: i for i in filtered}.values()


def _move_parent_boxes(
    obj: common.GenericElement,
    data: _elkjs.ELKInputData,
) -> None:
    owner_boxes: dict[str, _elkjs.ELKInputChild] = {
        child["id"]: child
        for child in data["children"]
        if child.get("children")
    }
    boxes_to_remove: list[str] = []
    for child in data["children"]:
        if not child.get("children"):
            continue

        owner = obj._model.by_uuid(child["id"])
        if (
            not (oowner := owner.owner)
            or isinstance(oowner, layers.oa.EntityPkg)
            or not (oowner_box := owner_boxes.get(oowner.uuid))
        ):
            continue

        oowner_box.setdefault("children", []).append(child)
        boxes_to_remove.append(child["id"])

    data["children"] = [
        b for b in data["children"] if b["id"] not in boxes_to_remove
    ]


def _move_edges(
    boxes: dict[str, _elkjs.ELKInputChild],
    connections: list[common.GenericElement],
    data: _elkjs.ELKInputData,
) -> None:
    owner_boxes: dict[str, _elkjs.ELKInputChild] = {
        uuid: box for uuid, box in boxes.items() if box.get("children")
    }
    edges_to_remove: list[str] = []

    for c in connections:
        source_owner_uuids = _get_all_owners(c.source)
        target_owner_uuids = _get_all_owners(c.target)
        common_owner_uuid = None
        for owner in source_owner_uuids:
            if owner in set(target_owner_uuids):
                common_owner_uuid = owner
                break

        if not common_owner_uuid or not (
            owner_box := owner_boxes.get(common_owner_uuid)
        ):
            continue

        for edge in data["edges"]:
            if edge["id"] == c.uuid:
                owner_box.setdefault("edges", []).append(edge)
                edges_to_remove.append(edge["id"])

    data["edges"] = [
        e for e in data["edges"] if e["id"] not in edges_to_remove
    ]


def _get_all_owners(obj: common.GenericElement) -> list[str]:
    owners = []
    current = obj
    while current is not None and not isinstance(current, layers.oa.EntityPkg):
        owners.append(current.uuid)
        try:
            current = current.owner
        except AttributeError:
            break
    return owners
