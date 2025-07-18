# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Default collector for the ContextDiagram.

Collection of
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that involve ports.
"""

from __future__ import annotations

import collections
import collections.abc as cabc
import itertools
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa

from . import _generic

if t.TYPE_CHECKING:
    from .. import context

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]


def collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect context data from exchanges of centric box."""
    visited_comps: set[str] = set()
    visited_ports: set[str] = set()
    visited_exchanges: set[str] = set()

    port_to_exchanges = get_port_to_exchange_mapping(diagram)
    stack: list[tuple[str, m.ModelElement]] = []
    stack.append(("comp", diagram.target))

    while stack:
        kind, current = stack.pop()

        if kind == "comp":
            if current.uuid in visited_comps:
                continue
            visited_comps.add(current.uuid)

            inc, out = _generic.port_collector(current, diagram.type)
            for port in itertools.chain(inc.values(), out.values()):
                if (
                    port.uuid not in visited_ports
                    and diagram.target.uuid
                    in set(_generic.get_all_owners(port))
                ):
                    visited_ports.add(port.uuid)
                    stack.append(("port", port))

            child_attr = get_child_attribute_name(current)
            for child in getattr(current, child_attr, []):
                if child.uuid not in visited_comps:
                    stack.append(("comp", child))

        elif kind == "port":
            for ex in port_context_collector(current, port_to_exchanges):
                if ex.uuid in visited_exchanges:
                    continue

                assert ex.source is not None
                assert ex.target is not None
                source_visited = ex.source.uuid in visited_ports
                target_visited = ex.target.uuid in visited_ports
                if source_visited and not target_visited:
                    visited_exchanges.add(ex.uuid)
                    yield ex
                    visited_ports.add(ex.target.uuid)
                    stack.append(("port", ex.target))
                    if ex.target.owner.uuid not in visited_comps:
                        stack.append(("comp", ex.target.owner))
                elif target_visited and not source_visited:
                    visited_exchanges.add(ex.uuid)
                    yield ex
                    visited_ports.add(ex.source.uuid)
                    stack.append(("port", ex.source))
                    if ex.source.owner.uuid not in visited_comps:
                        stack.append(("comp", ex.source.owner))
                elif source_visited and target_visited:
                    visited_exchanges.add(ex.uuid)
                    yield ex


def get_child_attribute_name(target: m.ModelElement) -> str:
    if isinstance(target, cs.Component):
        return "components"
    if isinstance(target, fa.AbstractFunction):
        return "functions"
    return ""


def get_port_to_exchange_mapping(
    diagram: context.ContextDiagram,
) -> dict[str, list[fa.FunctionalExchange | fa.ComponentExchange]]:
    """Get a mapping of port UUIDs to their exchanges."""
    all_exchanges = diagram.target._model.search(
        "ComponentExchange", "FunctionalExchange", "PhysicalLink"
    )
    port_to_exchanges: dict[
        str, list[fa.FunctionalExchange | fa.ComponentExchange]
    ] = collections.defaultdict(list)
    for exchange in all_exchanges:
        if exchange.source:
            port_uuid = exchange.source.uuid
            port_to_exchanges[port_uuid].append(exchange)

        if exchange.target:
            port_uuid = exchange.target.uuid
            port_to_exchanges[port_uuid].append(exchange)

    return port_to_exchanges


def port_context_collector(
    obj: m.ModelElement,
    port_to_exchanges: dict[
        str, list[fa.FunctionalExchange | fa.ComponentExchange]
    ],
) -> cabc.Iterator[fa.FunctionalExchange | fa.ComponentExchange]:
    """Collect context data from a physical port."""
    ports = set()
    links = set()

    def _collect(
        target: m.ModelElement,
    ) -> cabc.Iterator[fa.FunctionalExchange | fa.ComponentExchange]:
        if target.uuid in ports:
            return

        ports.add(target.uuid)
        for link in port_to_exchanges.get(target.uuid, []):
            if link.uuid in links:
                continue

            links.add(link.uuid)
            yield link
            assert link.source is not None
            yield from _collect(link.source)
            assert link.target is not None
            yield from _collect(link.target)

    yield from _collect(obj)


def functional_chain_collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect context data for a FunctionalChain."""
    if not isinstance(diagram.target, fa.FunctionalChain):
        return

    yield from diagram.target.involved


def physical_port_context_collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[fa.FunctionalExchange | fa.ComponentExchange]:
    """Collect context data from a physical port."""
    if not isinstance(diagram.target, cs.PhysicalPort):
        return

    port_to_exchanges = get_port_to_exchange_mapping(diagram)
    yield from port_context_collector(diagram.target, port_to_exchanges)
