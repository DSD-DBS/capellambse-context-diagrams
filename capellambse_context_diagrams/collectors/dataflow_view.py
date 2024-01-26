# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""..."""
from __future__ import annotations

import collections.abc as cabc
import typing as t

from capellambse import helpers
from capellambse.model import common
from capellambse.model.crosslayer import fa
from capellambse.model.layers import ctx, oa

from .. import _elkjs, context
from . import default, generic, makers, portless


def collector(
    diagram: context.ContextDiagram,
    params: dict[str, t.Any],
    attribute: str = "involved_functions",
    exchange_filter: cabc.Callable[
        [cabc.Iterable[fa.FunctionalExchange]],
        cabc.Iterable[fa.FunctionalExchange],
    ] = lambda exs: exs,
) -> _elkjs.ELKInputData:
    data = makers.make_diagram(diagram)
    functions = getattr(diagram.target, attribute)
    made_edges: set[str] = set()
    for fnc in functions:
        data["children"].append(fnc_box := makers.make_box(fnc))
        _ports = default.port_collector(fnc, diagram.type)
        connections = default.port_exchange_collector(
            _ports, filter=exchange_filter
        )
        in_ports: dict[str, fa.FunctionPort] = {}
        out_ports: dict[str, fa.FunctionPort] = {}
        for edge in connections:
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
        for ex in connections:
            if ex.uuid in made_edges:
                continue

            ex_data = generic.ExchangeData(ex, data, diagram.filters, params)
            generic.exchange_data_collector(ex_data)
            made_edges.add(ex.uuid)
            ex_datas.append(ex_data)
    return data


def only_involved(
    exchanges: cabc.Iterable[fa.FunctionalExchange],
    functions: cabc.Iterable[fa.FunctionalExchange],
) -> cabc.Iterable[fa.FunctionalExchange]:
    return [
        ex
        for ex in exchanges
        if ex.source.owner in functions and ex.target.owner in functions
    ]
