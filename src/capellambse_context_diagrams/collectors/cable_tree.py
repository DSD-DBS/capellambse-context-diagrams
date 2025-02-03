# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the CableTreeDiagram."""

from __future__ import annotations

import collections.abc as cabc
import typing as t

import capellambse.model as m

from .. import context
from . import _generic

if t.TYPE_CHECKING:
    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]


def collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect model elements for the CableTreeDiagram."""
    ports = set()
    links = set()

    def _collect(
        port_obj: m.ModelElement, filter: Filter = lambda i: i
    ) -> cabc.Iterator[m.ModelElement]:
        if port_obj.uuid in ports:
            return
        ports.add(port_obj.uuid)
        for link in filter(port_obj.links):
            if link.uuid in links:
                continue
            links.add(link.uuid)
            yield link
            yield from _collect(link.source, filter=filter)
            yield from _collect(link.target, filter=filter)

    src, tgt = diagram.target.source, diagram.target.target
    src_owner, tgt_owner = src.owner.uuid, tgt.owner.uuid
    if src_owner in set(_generic.get_all_owners(tgt)):
        common_owner = src_owner
    elif tgt_owner in set(_generic.get_all_owners(src)):
        common_owner = tgt_owner
    else:
        yield from _collect(src)
        return
    yield from _collect(
        src,
        filter=lambda items: (
            item
            for item in items
            if common_owner in set(_generic.get_all_owners(item))
        ),
    )
