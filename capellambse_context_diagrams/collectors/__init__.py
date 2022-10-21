# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Functionality for collection of model data from an instance of
[`MelodyModel`][capellambse.model.MelodyModel] and conversion of it into
[`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""
from __future__ import annotations

import collections.abc as cabc
import logging
import typing as t
from itertools import chain

import capellambse
from capellambse.model import common

from .. import _elkjs, diagram
from . import default, generic, portless

__all__ = ["get_elkdata"]
logger = logging.getLogger(__name__)

ContextInfo = t.Union[default.ContextInfo, portless.ContextInfo]
ContextCollector = cabc.Callable[
    [t.Iterable[common.GenericElement], common.GenericElement],
    t.Iterator[ContextInfo],
]

CONTEXT_DIRECTION_MAP = {
    "i": "input",
    "in": "input",
    "input": "input",
    "o": "output",
    "out": "output",
    "output": "output",
}


def get_elkdata(
    diag: diagram.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """High level collector function to collect needed data for ELK.

    Parameters
    ----------
    diag
        The [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram]
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
    context_description: dict[str, t.Any],
    context_collector: ContextCollector,
) -> cabc.Iterator[ContextInfo]:
    """Collect context for given ``target`` from ``context_description``."""
    subject = context_description.get("subject")
    if type(target).__name__ != subject:
        raise TypeError("Subject needs to match class-type of given target")

    exchanges = context_description.get("exchanges", [])
    contexts: list[list[ContextInfo]] = []
    for exchange in exchanges:
        candidates = set(model.search(*exchange["types"]))
        target_classes = _get_types(exchange["targets"], model)
        contexts.append(
            [
                _filter_connections_by_direction(ctx, exchange["direction"])
                for ctx in context_collector(candidates, target)
                if _filter_by_type(ctx, target_classes)
            ]
        )

    yield from chain.from_iterable(contexts)


def _filter_by_type(ctx: ContextInfo, types: cabc.Iterable[type]) -> bool:
    return any(isinstance(ctx.element, type) for type in types)


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
            if side != CONTEXT_DIRECTION_MAP[direction]:
                attr[side].clear()
    return ctx


def _get_types(
    targets: cabc.Iterable[str], model: capellambse.MelodyModel
) -> set[type]:
    return set((type(obj) for obj in model.search(*targets)))
