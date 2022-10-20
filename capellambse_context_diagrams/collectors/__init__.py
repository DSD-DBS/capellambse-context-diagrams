# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
Functionality for collection of model data from an instance of
[`MelodyModel`][capellambse.model.MelodyModel] and conversion of it into
[`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""
from __future__ import annotations

import collections.abc as cabc
import functools
import logging
import typing as t
from itertools import chain

import capellambse
from capellambse.model import common

from .. import _elkjs, diagram
from . import default, generic, portless

__all__ = ["get_elkdata"]
logger = logging.getLogger(__name__)
G = t.ParamSpec("G")
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
    target: G,
    context_description: dict[str, t.Any],
    context_collector: cabc.Callable[
        [t.Iterable[common.GenericElement], G, cabc.Callable[[G], bool]],
        t.Iterator[default.ContextInfo | portless.ContextInfo],
    ],
) -> cabc.Iterator[default.ContextInfo | portless.ContextInfo]:
    """Collect context for given ``target`` from ``context_description``."""
    subject = context_description.get("subject")
    if type(target).__name__ != subject:
        raise TypeError("Subject needs to match class-type of given target")

    def filter_by_type(
        ctx: default.ContextInfo | portless.ContextInfo,
        types: cabc.Iterable[type],
    ) -> bool:
        return any(isinstance(ctx.element, type) for type in types)

    direction_map = CONTEXT_DIRECTION_MAP
    contexts: list[list[default.ContextInfo | portless.ContextInfo]] = []
    exchanges = context_description.get("exchanges", [])
    for exchange in exchanges:
        candidates = set(model.search(*exchange["types"]))
        target_classes = get_types(exchange["targets"], model)
        target_filter = functools.partial(filter_by_type, types=target_classes)
        direction: str = exchange["direction"]

        def filter_connections_by_direction(
            ctx: default.ContextInfo | portless.ContextInfo,
        ) -> default.ContextInfo | portless.ContextInfo:
            if direction != "bi":
                for side in ctx.connections:
                    if side != direction_map[direction]:
                        ctx.connections[side].clear()
            return ctx

        contexts.append(
            [
                filter_connections_by_direction(ctx)
                for ctx in context_collector(candidates, target)
                if target_filter(ctx)
            ]
        )

    yield from chain.from_iterable(contexts)


def get_types(
    targets: cabc.Iterable[str], model: capellambse.MelodyModel
) -> set[type]:
    return set((type(obj) for obj in model.search(*targets)))
