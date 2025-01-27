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
    outside_components: dict[str, m.ModelElement] = {}

    def _collect(
        target: m.ModelElement,
        filter: Filter = lambda i: i,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in visited:
            return
        visited.add(target.uuid)

        inc, out = generic.port_collector(target, diagram.type)
        ports = generic.port_exchange_collector(
            (inc | out).values(), filter=filter
        )
        exchanges = chain.from_iterable(ports.values())
        for ex in exchanges:
            yield ex
            if ex.source.uuid in ports and ex.target.uuid not in ports:
                outside_components[ex.target.owner.uuid] = ex.target.owner
            elif ex.target.uuid in ports and ex.source.uuid not in ports:
                outside_components[ex.source.owner.uuid] = ex.source.owner

        if diagram._include_children_context or diagram._blackbox:
            for cmp in list(getattr(target, "components", [])):
                yield from _collect(cmp)

    def _collect_extended_context(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        yield from _collect(target)
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

    diagram._collect = _collect_extended_context(diagram.target)
    return custom.CustomCollector(diagram, params=params)()
