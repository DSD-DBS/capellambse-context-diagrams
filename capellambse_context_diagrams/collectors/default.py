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
from . import generic, makers


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    data = generic.collector(diagram, no_symbol=True)
    ports = port_collector(diagram.target)
    centerbox = data["children"][0]
    centerbox["ports"] = [makers.make_port(i.uuid) for i in ports]
    connections = port_exchange_collector(ports)
    for ex in connections:
        try:
            generic.exchange_data_collector(
                generic.ExchangeData(ex, data, diagram.filters, params)
            )
        except AttributeError:
            continue

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    made_boxes = {centerbox["id"]: centerbox}
    for i, local_ports, side in port_context_collector(connections, ports):
        _, label_height = helpers.get_text_extent(i.name)
        height = max(
            label_height + 2 * makers.LABEL_VPAD,
            makers.PORT_PADDING
            + (makers.PORT_SIZE + makers.PORT_PADDING) * len(local_ports),
        )
        if box := made_boxes.get(i.uuid):
            if box is centerbox:
                continue
            box["ports"].extend(
                [makers.make_port(j.uuid) for j in local_ports]
            )
            box["height"] += height
        else:
            box = makers.make_box(i, height=height)
            box["ports"] = [makers.make_port(j.uuid) for j in local_ports]
            made_boxes[i.uuid] = box

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    del made_boxes[centerbox["id"]]
    data["children"].extend(made_boxes.values())
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
    exchanges: list[common.GenericElement] = []
    for i in ports:
        try:
            exchanges.extend(getattr(i, "exchanges"))
        except AttributeError:
            pass
    return exchanges


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
    exchanges: t.Iterable[common.GenericElement],
    local_ports: t.Container[common.GenericElement],
) -> t.Iterator[ContextInfo]:
    """Collect the context objects.

    Parameters
    ----------
    exchanges
        The exchanges to look at to find new elements.
    local_ports
        Connectors/Ports lookup where `exchanges` is checked against.
        If an exchange connects via a port from `local_ports` it is
        collected.

    Returns
    -------
    contexts
        An iterator over
        [`ContextDiagram.ContextInfo`s][capellambse_context_diagrams.context.ContextDiagram].
    """

    ctx: dict[str, ContextInfo] = {}
    side: t.Literal["input", "output"]
    for exchange in exchanges:
        try:
            source, target = generic.collect_exchange_endpoints(exchange)
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
