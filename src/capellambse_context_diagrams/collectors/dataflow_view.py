# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the DataFlowDiagram."""

from __future__ import annotations

import collections.abc as cabc
import functools
import operator
import typing as t
from itertools import chain

import capellambse.model as m
from capellambse.metamodel import fa, oa

from .. import _elkjs, context
from . import default, generic, makers, portless

COLLECTOR_PARAMS: dict[m.DiagramType, dict[str, t.Any]] = {
    m.DiagramType.OAIB: {"attribute": "involved_activities"},
    m.DiagramType.SDFB: {
        "attribute": "involved_functions",
        "filter_attrs": ("source.owner", "target.owner"),
        "port_collector": default.port_collector,
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
    params: dict[str, t.Any],
    exchange_filter: cabc.Callable[
        [
            cabc.Iterable[fa.FunctionalExchange],
            cabc.Iterable[fa.FunctionalExchange],
            tuple[str, str],
        ],
        cabc.Iterable[fa.FunctionalExchange],
    ] = only_involved,
) -> _elkjs.ELKInputData:
    """Collect model elements through default or portless collectors."""
    return _collect_data(
        diagram, params, exchange_filter, **COLLECTOR_PARAMS[diagram.type]
    )


def _collect_data(
    diagram: context.ContextDiagram,
    params: dict[str, t.Any],
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
) -> _elkjs.ELKInputData:
    data = makers.make_diagram(diagram)
    elements = getattr(diagram.target, attribute)
    src_attr, trg_attr = filter_attrs
    source_getter = operator.attrgetter(src_attr)
    filter = functools.partial(
        exchange_filter,
        functions=elements,
        attributes=(src_attr, trg_attr),
    )  # type:ignore[call-arg]

    made_edges: set[str] = set()
    for elem in elements:
        data.children.append(box := makers.make_box(elem))
        if port_collector:
            _ports = port_collector(elem, diagram.type)
            connections = default.port_exchange_collector(
                _ports, filter=filter
            )
            edges = list(chain.from_iterable(connections.values()))
        else:
            edges = list(portless.get_exchanges(elem, filter=filter))

        in_elems: dict[str, fa.FunctionPort | oa.OperationalActivity] = {}
        out_elems: dict[str, fa.FunctionPort | oa.OperationalActivity] = {}
        for edge in edges:
            if source_getter(edge) == elem:
                out_elems.setdefault(edge.source.uuid, edge.source)
            else:
                in_elems.setdefault(edge.target.uuid, edge.target)

        if port_collector:
            box.ports = [
                makers.make_port(i.uuid)
                for i in (in_elems | out_elems).values()
            ]

        box.height += (makers.PORT_SIZE + 2 * makers.PORT_PADDING) * max(
            len(in_elems), len(out_elems)
        )
        ex_datas: list[generic.ExchangeData] = []
        for ex in edges:
            if ex.uuid in made_edges:
                continue

            ex_data = generic.ExchangeData(ex, data, diagram.filters, params)
            generic.exchange_data_collector(ex_data)
            made_edges.add(ex.uuid)
            ex_datas.append(ex_data)

    return data
