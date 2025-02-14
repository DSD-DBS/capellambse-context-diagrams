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
    """Collect context data from ports of centric box."""
    visited: set[str] = set()
    outside_nodes: dict[str, m.ModelElement] = {}
    edges: set[str] = set()

    def _collect(
        target: m.ModelElement,
        *,
        filter: Filter = lambda i: i,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in visited:
            return
        visited.add(target.uuid)

        inc, out = _generic.port_collector(target, diagram.type)
        ports = _generic.port_exchange_collector(
            (inc | out).values(), filter=filter
        )
        for ex in chain.from_iterable(ports.values()):
            if ex.uuid in edges:
                continue

            edges.add(ex.uuid)
            yield ex

            outside_port: m.ModelElement | None = None
            if diagram.target.uuid not in set(
                _generic.get_all_owners(ex.source)
            ):
                outside_nodes[ex.source.owner.uuid] = ex.source.owner
                outside_port = ex.source
            elif diagram.target.uuid not in set(
                _generic.get_all_owners(ex.target)
            ):
                outside_nodes[ex.target.owner.uuid] = ex.target.owner
                outside_port = ex.target

            if outside_port is not None:
                for ex in port_context_collector(outside_port):
                    if ex.uuid not in edges:
                        edges.add(ex.uuid)
                        yield ex

        child_attribute_name = get_child_attribute_name(target)
        for cmp in getattr(target, child_attribute_name, []):
            yield from _collect(cmp)

    yield from _collect(diagram.target)
    if not diagram._display_actor_relation:
        return

    on_copy = outside_nodes.copy()
    for cmp in on_copy.values():
        yield from _collect(
            cmp,
            filter=lambda items: (
                item
                for item in items
                if item.source.owner.uuid in visited
                and item.target.owner.uuid in visited
            ),
        )


def get_child_attribute_name(target: m.ModelElement) -> str:
    if isinstance(target, cs.Component):
        return "components"
    if isinstance(target, fa.Function):
        return "functions"
    return ""


def get_port_exchange_attribute_name(target: m.ModelElement) -> str:
    if isinstance(target, cs.PhysicalPort):
        return "links"
    if isinstance(target, fa.FunctionPort):
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
