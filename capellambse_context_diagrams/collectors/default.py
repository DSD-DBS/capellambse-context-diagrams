# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""
Collection of [`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
on diagrams that involve ports.
"""
from __future__ import annotations

import collections.abc as cabc
import typing as t

from capellambse import helpers
from capellambse.model import common
from capellambse.model.crosslayer import cs, fa
from capellambse.model.modeltypes import DiagramType as DT

from .. import _elkjs, context
from . import exchanges, generic, makers


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    data = generic.collector(diagram, no_symbol=True)
    ports = port_collector(diagram.target, diagram.type)
    centerbox = data["children"][0]
    centerbox["ports"] = [makers.make_port(i.uuid) for i in ports]
    connections = port_exchange_collector(ports)
    ex_datas: list[generic.ExchangeData] = []
    for ex in connections:
        if is_hierarchical := exchanges.is_hierarchical(ex, centerbox):
            if not diagram.include_inner_objects:
                continue

            elkdata: _elkjs.ELKInputData = centerbox
        else:
            elkdata = data
        try:
            ex_data = generic.ExchangeData(
                ex, elkdata, diagram.filters, params, is_hierarchical
            )
            generic.exchange_data_collector(ex_data)
            ex_datas.append(ex_data)
        except AttributeError:
            continue

    global_boxes = {centerbox["id"]: centerbox}
    if diagram.display_parent_relation:
        box = makers.make_box(
            diagram.target.parent,
            no_symbol=diagram.display_symbols_as_boxes,
            layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
        )
        box["children"] = [centerbox]
        del data["children"][0]
        global_boxes[diagram.target.parent.uuid] = box

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    child_boxes: list[_elkjs.ELKInputChild] = []
    for child, local_ports, side in port_context_collector(ex_datas, ports):
        _, label_height = helpers.get_text_extent(child.name)
        height = max(
            label_height + 2 * makers.LABEL_VPAD,
            makers.PORT_PADDING
            + (makers.PORT_SIZE + makers.PORT_PADDING) * len(local_ports),
        )
        if box := global_boxes.get(child.uuid):  # type: ignore[assignment]
            if box is centerbox:
                continue
            box.setdefault("ports", []).extend(
                [makers.make_port(j.uuid) for j in local_ports]
            )
            box["height"] += height
        else:
            box = makers.make_box(
                child,
                height=height,
                no_symbol=diagram.display_symbols_as_boxes,
            )
            box["ports"] = [makers.make_port(j.uuid) for j in local_ports]
            if child.parent.uuid == centerbox["id"]:
                child_boxes.append(box)
            else:
                global_boxes[child.uuid] = box

        if diagram.display_parent_relation:
            if child == diagram.target.parent:
                _move_edge_to_local_edges(
                    box, connections, local_ports, diagram, data
                )
            elif child.parent == diagram.target.parent:
                parent_box = global_boxes[child.parent.uuid]
                parent_box.setdefault("children", []).append(
                    global_boxes.pop(child.uuid)
                )
                for label in parent_box["labels"]:
                    label["layoutOptions"] = (
                        makers.CENTRIC_LABEL_LAYOUT_OPTIONS
                    )

                _move_edge_to_local_edges(
                    parent_box, connections, local_ports, diagram, data
                )

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del global_boxes[centerbox["id"]]
    data["children"].extend(global_boxes.values())
    if child_boxes:
        centerbox["children"] = child_boxes
        centerbox["width"] = makers.EOI_WIDTH
        for label in centerbox.get("labels", []):
            label.setdefault("layoutOptions", {}).update(
                makers.DEFAULT_LABEL_LAYOUT_OPTIONS
            )

    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    return data


def _move_edge_to_local_edges(
    box: _elkjs.ELKInputChild,
    connections: list[common.GenericElement],
    local_ports: list[common.GenericElement],
    diagram: context.ContextDiagram,
    data: _elkjs.ELKInputData,
) -> None:
    edges_to_remove: list[str] = []
    for c in connections:
        if (
            c.target in local_ports
            and c.source in diagram.target.ports
            or c.source in local_ports
            and c.target in diagram.target.ports
        ):
            for edge in data["edges"]:
                if edge["id"] == c.uuid:
                    box.setdefault("edges", []).append(edge)
                    edges_to_remove.append(edge["id"])

    data["edges"] = [
        e for e in data["edges"] if e["id"] not in edges_to_remove
    ]


def port_collector(
    target: common.GenericElement | common.ElementList, diagram_type: DT
) -> list[common.GenericElement]:
    """Savely collect ports from `target`."""

    def __collect(target):
        all_ports: list[common.GenericElement] = []
        for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram_type]:
            try:
                ports = getattr(target, attr)
                if ports and isinstance(
                    ports[0],
                    (fa.FunctionPort, fa.ComponentPort, cs.PhysicalPort),
                ):
                    all_ports.extend(ports)
            except AttributeError:
                pass
        return all_ports

    if isinstance(target, cabc.Iterable):
        assert not isinstance(target, common.GenericElement)
        all_ports: list[common.GenericElement] = []
        for obj in target:
            all_ports.extend(__collect(obj))
    else:
        all_ports = __collect(target)
    return all_ports


def port_exchange_collector(
    ports: t.Iterable[common.GenericElement],
    filter: cabc.Callable[
        [cabc.Iterable[common.GenericElement]],
        cabc.Iterable[common.GenericElement],
    ] = lambda i: i,
) -> list[common.GenericElement]:
    """Collect exchanges from `ports` savely."""
    edges: list[common.GenericElement] = []
    for i in ports:
        try:
            filtered = filter(getattr(i, "exchanges"))
            edges.extend(filtered)
        except AttributeError:
            pass
    return edges


class ContextInfo(t.NamedTuple):
    """ContextInfo data."""

    element: common.GenericElement
    """An element of context."""
    ports: list[common.GenericElement]
    """The context element's relevant ports.

    This list only contains ports that at least one of the exchanges
    passed into ``collect_exchanges`` sees.
    """
    side: t.Literal["input", "output"]
    """Whether this is an input or output to the element of interest."""


def port_context_collector(
    exchange_datas: t.Iterable[generic.ExchangeData],
    local_ports: t.Container[common.GenericElement],
) -> t.Iterator[ContextInfo]:
    """Collect the context objects.

    Parameters
    ----------
    exchange_datas
        The ``ExchangeData``s to look at to find new elements.
    local_ports
        Connectors/Ports lookup where ``exchange_datas`` is checked
        against. If an exchange connects via a port from ``local_ports``
        it is collected.

    Returns
    -------
    contexts
        An iterator over
        [`ContextDiagram.ContextInfo`s][capellambse_context_diagrams.context.ContextDiagram].
    """

    ctx: dict[str, ContextInfo] = {}
    side: t.Literal["input", "output"]
    for exd in exchange_datas:
        try:
            source, target = generic.collect_exchange_endpoints(exd)
        except AttributeError:
            continue

        if source in local_ports:
            port = target
            side = "output"
        elif target in local_ports:
            port = source
            side = "input"
        else:
            continue

        try:
            owner = port.owner  # type: ignore[attr-defined]
        except AttributeError:
            continue

        info = ContextInfo(owner, [], side)
        info = ctx.setdefault(owner.uuid, info)
        if port not in info.ports:
            info.ports.append(port)

    return iter(ctx.values())
