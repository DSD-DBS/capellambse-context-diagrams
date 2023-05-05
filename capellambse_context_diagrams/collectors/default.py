# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
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

from .. import _elkjs, context
from . import exchanges, generic, makers


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    data = generic.collector(diagram, no_symbol=True)
    ports = port_collector(diagram.target)
    centerbox = data["children"][0]
    centerbox["ports"] = [makers.make_port(i.uuid) for i in ports]
    connections = port_exchange_collector(ports)
    ex_datas = list[generic.ExchangeData]()
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

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    global_boxes = {centerbox["id"]: centerbox}
    child_boxes = list[_elkjs.ELKInputChild]()
    for i, local_ports, side in port_context_collector(ex_datas, ports):
        _, label_height = helpers.get_text_extent(i.name)
        height = max(
            label_height + 2 * makers.LABEL_VPAD,
            makers.PORT_PADDING
            + (makers.PORT_SIZE + makers.PORT_PADDING) * len(local_ports),
        )
        if box := global_boxes.get(i.uuid):
            if box is centerbox:
                continue
            box["ports"].extend(
                [makers.make_port(j.uuid) for j in local_ports]
            )
            box["height"] += height
        else:
            box = makers.make_box(i, height=height)
            box["ports"] = [makers.make_port(j.uuid) for j in local_ports]
            if i.parent.uuid == centerbox["id"]:
                child_boxes.append(box)
            else:
                global_boxes[i.uuid] = box

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del global_boxes[centerbox["id"]]
    data["children"].extend(global_boxes.values())
    if child_boxes:
        centerbox["children"] = child_boxes
        centerbox["width"] = makers.EOI_WIDTH

    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    return data


def port_collector(
    target: common.GenericElement | common.ElementList,
) -> list[common.GenericElement]:
    """Savely collect ports from `target`."""

    def __collect(target):
        all_ports: list[common.GenericElement] = []
        for attr in generic.CONNECTOR_ATTR_NAMES | {"ports"}:
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
) -> list[common.GenericElement]:
    """Collect exchanges from `ports` savely."""
    edges: list[common.GenericElement] = []
    for i in ports:
        try:
            edges.extend(getattr(i, "exchanges"))
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
