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

    second_param = target
    # pylint: disable=comparison-with-callable
    if context_collector == default.port_context_collector:
        second_param = default.port_collector(target)

    exchange: dict[str, t.Any]
    for exchange in context_description.get("exchanges", []):
        ex_descr = data.ExchangeDescription(
            targets=data.get_target_descriptions(exchange["targets"]),
            types=exchange["types"],
            model=model,
            direction=exchange.get("direction", "bi"),
        )
        if context_collector is None:
            context_collector = generate_ctx_collector(target, ex_descr)

        context_collection = context_collector(
            ex_descr.candidates, second_param
        )

        for context in context_collection:
            if _filter_by_target_description(context, ex_descr.target_types):
                yield _apply_mods(context, exchange)


def generate_ctx_collector(
    target: common.GenericElement, ex_ctx_desc: dict[str, t.Any]
) -> ContextCollector:
    """Return a context collector function."""
    types = set(ex_ctx_desc.get("types", []))
    if not types:
        raise data.InvalidContextDescription(
            "Invalid exchanges description: List of 'types' required"
        )
    targets = ex_ctx_desc.get("targets", [])
    if not target:
        raise data.InvalidContextDescription(
            "Invalid exchanges description: List of 'targets' required"
        )

    for path, ttype in _extract_targets(targets):
        operator.attrgetter(path)

    def collect_exchange_endpoints(
        exchange: common.GenericElement,
    ) -> tuple[common.GenericElement, common.GenericElement]:
        if ex_ctx_desc.get("sources", []):
            logger.debug("Individual source endpoint translation.")
            ...
        else:
            logger.debug("Uniform source and target endpoints translation.")

    def context_collector(
        exchanges: t.Iterable[common.GenericElement],
        obj_oi: common.GenericElement,
    ) -> t.Iterator[ContextInfo]:
        ctx: dict[str, ContextInfo] = {}
        side: t.Literal["input", "output"]
        for exchange in exchanges:
            if type(exchange).__name__ not in types:
                continue

            try:
                source, target = collect_exchange_endpoints(exchange)
            except AttributeError:
                continue

            if source == obj_oi:
                obj = target
                side = "output"
            elif target == obj_oi:
                obj = source
                side = "input"
            else:
                continue

            info = ContextInfo(
                element=obj, connections={"output": [], "input": []}
            )
            info = ctx.setdefault(obj.uuid, info)
            if exchange not in info.connections[side]:
                info.connections[side].append(exchange)

        return iter(ctx.values())

    return context_collector


def _filter_by_target_description(
    ctx: ContextInfo, types: cabc.Iterable[type[common.ModelObject]]
) -> bool:
    return any(isinstance(ctx.element, type) for type in types)


def _apply_mods(
    ctx: ContextInfo, exchange_data: dict[str, t.Any]
) -> ContextInfo:
    if direction := exchange_data.get("direction"):
        ctx = _filter_connections_by_direction(ctx, direction)
    return ctx


def _filter_connections_by_direction(
    ctx: ContextInfo, direction: str
) -> ContextInfo:
    try:
        attr = ctx.connections  # type: ignore[union-attr]
    except AttributeError:
        assert isinstance(ctx, default.ContextInfo)
        attr = ctx.ports

    if direction != "bi":
        for side in attr:
            if side != direction:
                attr[side].clear()
    return ctx
