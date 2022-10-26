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
    context_collector: ContextCollector,
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

        context_collection = context_collector(
            ex_descr.candidates, second_param
        )

        for context in context_collection:
            if _filter_by_target_description(context, ex_descr.target_types):
                yield _apply_mods(context, exchange)


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
