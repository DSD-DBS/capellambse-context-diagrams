# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Default collector for the ContextDiagram.

Collection of
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that involve ports.
"""

from __future__ import annotations

import collections.abc as cabc
import typing as t
from itertools import chain

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

    stack: list[tuple[str, m.ModelElement]] = []
    stack.append(("comp", diagram.target))

    while stack:
        kind, current = stack.pop()

        if kind == "comp":
            if current.uuid in visited_comps:
                continue
            visited_comps.add(current.uuid)

            inc, out = _generic.port_collector(current, diagram.type)
            for port in chain(inc.values(), out.values()):
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
            for ex in port_context_collector(current):
                if ex.uuid in visited_exchanges:
                    continue

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
    if isinstance(target, fa.Function):
        return "functions"
    return ""


def get_port_exchange_attribute_name(target: m.ModelElement) -> str:
    if isinstance(target, cs.PhysicalPort):
        return "links"
    if isinstance(target, fa.FunctionPort | fa.ComponentPort):
        return "exchanges"
    return ""


def port_context_collector(
    obj: context.ContextDiagram | m.ModelElement,
) -> cabc.Iterator[fa.AbstractExchange]:
    """Collect context data from a physical port."""
    ports = set()
    links = set()

    def _collect(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in ports:
            return
        ports.add(target.uuid)
        exchange_attribute_name = get_port_exchange_attribute_name(target)
        for link in getattr(target, exchange_attribute_name, []):
            if link.uuid in links:
                continue
            links.add(link.uuid)
            yield link
            yield from _collect(link.source)
            yield from _collect(link.target)

    if isinstance(obj, m.ModelElement):
        yield from _collect(obj)  # type: ignore[misc]
        return

    yield from _collect(obj.target)  # type: ignore[misc]
