# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines the collectors for the DataFlowDiagram."""
from __future__ import annotations

import collections.abc as cabc
import functools
import operator
import typing as t
from itertools import chain

from capellambse.model import modeltypes
from capellambse.model.crosslayer import fa
from capellambse.model.layers import oa

from .. import _elkjs, context
from . import default, generic, makers, portless


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
    """Main collector that calls either default or portless collectors."""
    return COLLECTORS[diagram.type](diagram, params, exchange_filter)


def collector_portless(
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
    attribute: str = "involved_activities",
) -> _elkjs.ELKInputData:
    """Collector function for the operational layer."""
    data = makers.make_diagram(diagram)
    activities = getattr(diagram.target, attribute)
    filter = functools.partial(
        exchange_filter,
        functions=activities,
        attributes=("source", "target"),
    )
    made_edges: set[str] = set()
    for act in activities:
        data["children"].append(act_box := makers.make_box(act))
        connections = list(portless.get_exchanges(act, filter=filter))

        in_act: dict[str, oa.OperationalActivity] = {}
        out_act: dict[str, oa.OperationalActivity] = {}
        for edge in connections:
            if edge.source == act:
                out_act.setdefault(edge.source.uuid, edge.source)
            else:
                in_act.setdefault(edge.target.uuid, edge.target)

        act_box["height"] += (
            makers.PORT_SIZE + 2 * makers.PORT_PADDING
        ) * max(len(in_act), len(out_act))

        ex_datas: list[generic.ExchangeData] = []
        for ex in connections:
            if ex.uuid in made_edges:
                continue

            ex_data = generic.ExchangeData(ex, data, diagram.filters, params)
            generic.exchange_data_collector(ex_data)
            made_edges.add(ex.uuid)
            ex_datas.append(ex_data)

    return data


def collector_default(
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
    attribute: str = "involved_functions",
) -> _elkjs.ELKInputData:
    """Collector for all other layers than operational architecture."""
    data = makers.make_diagram(diagram)
    functions = getattr(diagram.target, attribute)
    filter = functools.partial(
        exchange_filter,
        functions=functions,
        attributes=("source.owner", "target.owner"),
    )
    made_edges: set[str] = set()
    for fnc in functions:
        data["children"].append(fnc_box := makers.make_box(fnc))
        _ports = default.port_collector(fnc, diagram.type)
        connections = default.port_exchange_collector(_ports, filter=filter)
        in_ports: dict[str, fa.FunctionPort] = {}
        out_ports: dict[str, fa.FunctionPort] = {}
        for edge in (edges := list(chain.from_iterable(connections.values()))):
            if edge.source.owner == fnc:
                out_ports.setdefault(edge.source.uuid, edge.source)
            else:
                in_ports.setdefault(edge.target.uuid, edge.target)

        fnc_box["ports"] = [
            makers.make_port(i.uuid) for i in (in_ports | out_ports).values()
        ]
        fnc_box["height"] += (
            makers.PORT_SIZE + 2 * makers.PORT_PADDING
        ) * max(len(in_ports), len(out_ports))

        ex_datas: list[generic.ExchangeData] = []
        for ex in edges:
            if ex.uuid in made_edges:
                continue

            ex_data = generic.ExchangeData(ex, data, diagram.filters, params)
            generic.exchange_data_collector(ex_data)
            made_edges.add(ex.uuid)
            ex_datas.append(ex_data)
    return data


COLLECTORS: dict[modeltypes.DiagramType, cabc.Callable] = {
    modeltypes.DiagramType.OAIB: collector_portless,
    modeltypes.DiagramType.SDFB: collector_default,
}
"""Collector registry."""
