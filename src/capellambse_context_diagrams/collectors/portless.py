# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for portless ContextDiagrams.

This collector is used to collect
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that don't involve ports or any connectors.
"""

from __future__ import annotations

import collections.abc as cabc
import typing as t
from itertools import chain

import capellambse.model as m
from capellambse.metamodel import oa, sa

from .. import context
from . import _generic

SOURCE_ATTR_NAMES = frozenset(("parent",))
TARGET_ATTR_NAMES = frozenset(("involved", "capability"))


def collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect context data from exchanges of centric box.

    This is the special context collector for the operational
    architecture layer diagrams (diagrams where elements don't exchange
    via ports/connectors).
    """
    yield from get_exchanges(diagram.target)


def collect_exchange_endpoints(
    e: m.ModelElement,
) -> tuple[m.ModelElement, m.ModelElement]:
    """Safely collect exchange endpoints from `e`."""

    def _get(e: m.ModelElement, attrs: frozenset[str]) -> m.ModelElement:
        for attr in attrs:
            try:
                obj = getattr(e, attr)
                assert isinstance(obj, m.ModelElement)
                return obj
            except AttributeError:
                continue
        raise AttributeError()

    try:
        return _get(e, SOURCE_ATTR_NAMES), _get(e, TARGET_ATTR_NAMES)
    except AttributeError:
        pass
    return _generic.collect_exchange_endpoints(e)


def get_exchanges(
    obj: m.ModelElement,
    filter: cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ] = lambda i: i,
) -> t.Iterator[t.Any]:
    """Yield exchanges safely.

    Yields exchanges from ``.related_exchanges`` or exclusively by
    ``obj`` classtype:
        * Capabilities:
            * ``.extends``,
            * ``.includes``,
            * ``.generalizes`` and their reverse
            * ``.included_by``,
            * ``.extended_by``,
            * ``.generalized_by`` and optionally
            * ``.entity_involvements`` (Operational)
            * ``.component_involvements`` and ``.incoming_exploitations``
              (System)
        * Mission:
            * ``.involvements`` and
            * ``.exploitations``.
    """
    is_op_capability = isinstance(obj, oa.OperationalCapability)
    is_capability = isinstance(obj, sa.Capability)
    if is_op_capability or is_capability:
        exchanges = [
            obj.includes,
            obj.extends,
            obj.generalizes,
            obj.included_by,
            obj.extended_by,
            obj.generalized_by,
        ]
    elif isinstance(obj, sa.Mission):
        exchanges = [obj.involvements, obj.exploitations]
    else:
        exchanges = [obj.related_exchanges]

    if is_op_capability:
        exchanges += [obj.entity_involvements]
    elif is_capability:
        exchanges += [obj.component_involvements, obj.incoming_exploitations]

    filtered = filter(chain.from_iterable(exchanges))
    yield from {i.uuid: i for i in filtered}.values()
