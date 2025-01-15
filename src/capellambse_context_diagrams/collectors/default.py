# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Default collector for the ContextDiagram.

Collection of
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that involve ports.
"""

from __future__ import annotations

import collections.abc as cabc
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa
from capellambse.model import DiagramType as DT

from .. import _elkjs
from . import custom, generic

if t.TYPE_CHECKING:
    from .. import context

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    visited: set[str] = set()
    edges: set[str] = set()

    def _collect(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in visited:
            return
        visited.add(target.uuid)
        for port in (
            list(getattr(target, "inputs", []))
            + list(getattr(target, "outputs", []))
            + list(getattr(target, "ports", []))
            + list(getattr(target, "physical_ports", []))
        ):
            for exchange in list(getattr(port, "exchanges", [])) + list(
                getattr(port, "links", [])
            ):
                if exchange.uuid in edges:
                    continue
                edges.add(exchange.uuid)
                yield exchange
        for cmp in list(getattr(target, "components", [])):
            yield from _collect(cmp)

    diagram._collect = _collect(diagram.target)
    processor = custom.CustomCollector(diagram, params=params)
    processor()
    return processor.data


def port_collector(
    target: m.ModelElement | m.ElementList, diagram_type: DT
) -> tuple[dict[str, m.ModelElement], dict[str, m.ModelElement]]:
    """Collect ports from `target` savely."""

    def __collect(target):
        port_types = fa.FunctionPort | fa.ComponentPort | cs.PhysicalPort
        incoming_ports: dict[str, m.ModelElement] = {}
        outgoing_ports: dict[str, m.ModelElement] = {}
        for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram_type]:
            try:
                ports = getattr(target, attr)
                if not ports or not isinstance(ports[0], port_types):
                    continue

                if attr == "inputs":
                    incoming_ports.update({p.uuid: p for p in ports})
                elif attr == "ports":
                    for port in ports:
                        if port.direction == "IN":
                            incoming_ports[port.uuid] = port
                        else:
                            outgoing_ports[port.uuid] = port
                else:
                    outgoing_ports.update({p.uuid: p for p in ports})
            except AttributeError:
                pass
        return incoming_ports, outgoing_ports

    if isinstance(target, cabc.Iterable):
        assert not isinstance(target, m.ModelElement)
        incoming_ports: dict[str, m.ModelElement] = {}
        outgoing_ports: dict[str, m.ModelElement] = {}
        for obj in target:
            inc, out = __collect(obj)
            incoming_ports.update(inc)
            outgoing_ports.update(out)
    else:
        incoming_ports, outgoing_ports = __collect(target)
    return incoming_ports, outgoing_ports


def _extract_edges(
    obj: m.ModelElement,
    attribute: str,
    filter: Filter,
) -> cabc.Iterable[m.ModelElement]:
    return filter(getattr(obj, attribute, []))


def port_exchange_collector(
    ports: t.Iterable[m.ModelElement],
    filter: Filter = lambda i: i,
) -> dict[str, list[fa.AbstractExchange]]:
    """Collect exchanges from `ports` savely."""
    edges: dict[str, list[fa.AbstractExchange]] = {}

    for port in ports:
        if exs := _extract_edges(port, "exchanges", filter):
            edges[port.uuid] = t.cast(list[fa.AbstractExchange], exs)
            continue

        if links := _extract_edges(port, "links", filter):
            edges[port.uuid] = t.cast(list[fa.AbstractExchange], links)

    return edges


class ContextInfo(t.NamedTuple):
    """ContextInfo data."""

    element: m.ModelElement
    """An element of context."""
    ports: list[m.ModelElement]
    """The context element's relevant ports.

    This list only contains ports that at least one of the exchanges
    passed into ``collect_exchanges`` sees.
    """
