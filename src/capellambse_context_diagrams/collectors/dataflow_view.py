# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the DataFlowDiagram."""

from __future__ import annotations

import collections.abc as cabc
import functools
import operator
import typing as t
from itertools import chain

import capellambse.model as m
from capellambse.metamodel import fa

from .. import context
from . import _generic, portless

COLLECTOR_PARAMS: dict[m.DiagramType, dict[str, t.Any]] = {
    m.DiagramType.OAIB: {"attribute": "involved_activities"},
    m.DiagramType.SDFB: {
        "attribute": "involved_functions",
        "filter_attrs": ("source.owner", "target.owner"),
        "port_collector": _generic.port_collector,
    },
}


def only_involved(
    exchanges: cabc.Iterable[fa.FunctionalExchange],
    functions: cabc.Iterable[fa.FunctionalExchange],
    attributes: tuple[str, str],
) -> cabc.Iterable[fa.FunctionalExchange]:
    """Exchange filter function for collecting edges."""
    src_attr, trg_attr = attributes
    src_getter = operator.attrgetter(src_attr)
    trg_getter = operator.attrgetter(trg_attr)
    return [
        ex
        for ex in exchanges
        if src_getter(ex) in functions and trg_getter(ex) in functions
    ]


def collector(
    diagram: context.ContextDiagram,
    exchange_filter: cabc.Callable[
        [
            cabc.Iterable[fa.FunctionalExchange],
            cabc.Iterable[fa.FunctionalExchange],
            tuple[str, str],
        ],
        cabc.Iterable[fa.FunctionalExchange],
    ] = only_involved,
) -> cabc.Iterator[m.ModelElement]:
    """Collect model elements through default or portless collectors."""
    yield from _collect_data(
        diagram, exchange_filter, **COLLECTOR_PARAMS[diagram.type]
    )


def _collect_data(
    diagram: context.ContextDiagram,
    exchange_filter: cabc.Callable[
        [
            cabc.Iterable[fa.FunctionalExchange],
            cabc.Iterable[fa.FunctionalExchange],
            tuple[str, str],
        ],
        cabc.Iterable[fa.FunctionalExchange],
    ],
    attribute: str,
    filter_attrs: tuple[str, str] = ("source", "target"),
    port_collector: cabc.Callable | None = None,
) -> cabc.Iterator[m.ModelElement]:
    elements = getattr(diagram.target, attribute)
    src_attr, trg_attr = filter_attrs
    filter = functools.partial(
        exchange_filter,
        functions=elements,
        attributes=(src_attr, trg_attr),
    )  # type:ignore[call-arg]

    for elem in elements:
        yield elem
        if port_collector:
            _ports = port_collector(elem, diagram.type)
            connections = _generic.port_exchange_collector(
                _ports, filter=filter
            )
            yield from chain.from_iterable(connections.values())
        else:
            diagram._is_portless = True
            yield from portless.get_exchanges(elem, filter=filter)
