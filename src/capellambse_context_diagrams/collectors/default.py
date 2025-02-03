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

from ..builders import default as db
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
    outside_components: dict[str, m.ModelElement] = {}

    def _collect(
        target: m.ModelElement,
        *,
        filter: Filter = lambda i: i,
        include_children: bool = False,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in visited:
            return
        visited.add(target.uuid)

        inc, out = _generic.port_collector(target, diagram.type)
        ports = _generic.port_exchange_collector(
            (inc | out).values(), filter=filter
        )
        exchanges = chain.from_iterable(ports.values())
        for ex in exchanges:
            yield ex
            if ex.source.uuid in ports and ex.target.uuid not in ports:
                outside_components[ex.target.owner.uuid] = ex.target.owner
            elif ex.target.uuid in ports and ex.source.uuid not in ports:
                outside_components[ex.source.owner.uuid] = ex.source.owner

        if include_children:
            for cmp in list(getattr(target, "components", [])):
                yield from _collect(cmp)

    yield from _collect(
        diagram.target,
        include_children=diagram._include_children_context
        or diagram._mode in (db.MODE.WHITEBOX.name, db.MODE.GRAYBOX.name),
    )
    if not diagram._display_actor_relation:
        return
    oc_copy = outside_components.copy()
    for cmp in oc_copy.values():
        yield from _collect(
            cmp,
            filter=lambda items: (
                item
                for item in items
                if item.source.owner.uuid in oc_copy
                and item.target.owner.uuid in oc_copy
            ),
        )


def physical_port_context_collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect context data from a physical port."""
    ports = set()
    links = set()

    def _collect(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in ports:
            return
        ports.add(target.uuid)
        for link in target.links:
            if link.uuid in links:
                continue
            links.add(link.uuid)
            yield link
            yield from _collect(link.source)
            yield from _collect(link.target)

    yield from _collect(diagram.target)
