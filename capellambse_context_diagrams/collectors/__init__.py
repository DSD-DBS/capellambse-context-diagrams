# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Functionality for collection of model data from an instance of
[`MelodyModel`][capellambse.model.MelodyModel] and conversion of it into
[`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""
from __future__ import annotations

import collections.abc as cabc
import logging
import operator
import typing as t

import capellambse
from capellambse.model import common

from .. import _elkjs, diagram
from . import data, default, generic, portless

__all__ = ["get_elkdata"]
logger = logging.getLogger(__name__)

ContextInfo = t.Union[default.ContextInfo, portless.ContextInfo]
ContextCollector = cabc.Callable[
    [t.Iterable[common.GenericElement], common.GenericElement],
    t.Iterator[ContextInfo],
]


def get_elkdata(
    diag: diagram.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """High level collector function to collect needed data for ELK.

    Parameters
    ----------
    diag
        The [`ContextDiagram`][capellambse_context_diagrams.diagram.ContextDiagram]
        instance to get the
        [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
        for.
    params
        Optional render params dictionary.

    Returns
    -------
    elkdata
        The data that can be fed into elkjs.
    """

    if diag.type in generic.PORTLESS_DIAGRAM_TYPES:
        collector = portless.collector
    else:
        collector = default.collector

    return collector(diag, params)


def collect_free_context(
    model: capellambse.MelodyModel,
    target: common.GenericElement,
    context_description: cabc.Mapping[str, t.Any],
    context_collector: ContextCollector | None = None,
) -> cabc.Iterator[ContextInfo]:
    """Collect the context for the diagram target from a description."""
    subject = context_description.get("subject")
    if type(target).__name__ != subject:
        raise TypeError("Subject needs to match class-type of given target")

    cparam = target
    # pylint: disable=comparison-with-callable
    if context_collector == default.port_context_collector:
        cparam = default.port_collector(target)

    no_context_collector_given = context_collector is None
    exchange: dict[str, t.Any]
    for exchange in context_description.get("exchanges", []):
        ex_descr = data.ExchangeDescription.from_dict(exchange, model, subject)
        if no_context_collector_given:
            context_collector = generate_ctx_collector(ex_descr)

        assert context_collector is not None
        context_collection = list(
            context_collector(ex_descr.candidates, cparam)
        )
        for context in context_collection:
            yield _apply_mods(context, ex_descr)


def generate_ctx_collector(
    ex_description: data.ExchangeDescription,
) -> ContextCollector:
    """Return a context collector function."""
    SourceAndTargetTuple = tuple[common.GenericElement, common.GenericElement]

    def collect_exchange_endpoints(
        exchange: common.GenericElement,
    ) -> SourceAndTargetTuple:
        """Return endpoints for given exchange."""
        queries = ex_description.target_queries[type(exchange)]
        source: common.ModelObject = exchange
        target: common.ModelObject = exchange
        for source_query, target_query in queries:
            source = source_query(source)
            target = target_query(target)

        if not isinstance(source, ex_description.source_end_types):
            raise data.InvalidContextDescription(
                f"Invalid terminal 'type' in 'targets' for source: {source!r}"
            )

        if not isinstance(target, ex_description.target_end_types):
            raise data.InvalidContextDescription(
                f"Invalid terminal 'type' in 'targets' for target: {target!r}"
            )

        return source, target

    def context_collector(
        exchanges: t.Iterable[common.GenericElement],
        obj_oi: common.GenericElement,
    ) -> t.Iterator[ContextInfo]:
        ctx: dict[str, ContextInfo] = {}
        side: t.Literal["input", "output"]
        for exchange in exchanges:
            if type(exchange).__name__ not in ex_description.types:
                continue

            try:
                source, target = collect_exchange_endpoints(exchange)
            except AttributeError as error:
                logger.exception("Invalid model query: %s", error.args[0])
                continue
            except data.InvalidContextDescription:
                continue

            if source == obj_oi:
                obj = target
                side = "output"
            elif target == obj_oi:
                obj = source
                side = "input"
            else:
                continue

            info = portless.ContextInfo(
                element=obj, connections={"output": [], "input": []}
            )
            info = ctx.setdefault(obj.uuid, info)
            if exchange not in info.connections[side]:
                info.connections[side].append(exchange)

        return iter(ctx.values())

    return context_collector


def _apply_mods(
    ctx: ContextInfo, ex_description: data.ExchangeDescription
) -> ContextInfo:
    if ex_description.direction != "bi":
        ctx = _filter_connections_by_direction(ctx, ex_description.direction)

    return ctx


def _filter_connections_by_direction(
    ctx: ContextInfo, direction: str
) -> ContextInfo:
    try:
        attr = ctx.connections  # type: ignore[union-attr]
    except AttributeError:
        assert isinstance(ctx, default.ContextInfo)
        attr = ctx.ports

    for side in attr:
        if side != direction:
            attr[side].clear()

    return ctx
