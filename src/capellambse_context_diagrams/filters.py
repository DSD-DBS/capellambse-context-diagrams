# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions and registry for filter functionality."""

from __future__ import annotations

import collections.abc as cabc
import logging
import re
import typing as t

import capellambse.model as m
from capellambse.metamodel import fa

SHOW_EX_ITEMS = "show.functional.exchanges.exchange.items.filter"
"""Show the name of `ComponentExchange` or `FunctionalExchange` and its
`ExchangeItems` wrapped in [E1,...] and separated by ',' - filter in Capella.
"""
EX_ITEMS = "show.exchange.items.filter"
"""Show `ExchangeItems` wrapped in [E1,...] and separated by ',' - filter
in Capella.
"""
EX_ITEMS_OR_EXCH = (
    "capellambse_context_diagrams-show.exchanges.or.exchange.items.filter"
)
"""Show the names of `ExchangeItem`s wrapped in [E1,...] and separated by ','
- Custom filter or the name of the `ComponentExchange` or `FunctionalExchange`,
not available in Capella.
"""
NO_UUID = "capellambse_context_diagrams-hide.uuids.filter"
"""Filter out UUIDs from label text."""
SYSTEM_EX_RELABEL = (
    "capellambse_context_diagrams-relabel.system.analysis.exchange"
)
"""Relabel exchanges from the SystemAnalysis layer.

E.g. « i » is converted to includes or involves, based on the type.
"""


logger = logging.getLogger(__name__)

UUID_PTRN = re.compile(
    r"\s*\([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\)"
)
"""Regular expression pattern for UUIDs of `ModelObject`s."""
LABEL_CONVERSION: t.Final[dict[str, str]] = {
    "AbstractCapabilityExtend": "extends",
    "AbstractCapabilityGeneralization": "specializes",
    "AbstractCapabilityInclude": "includes",
    "CapabilityExploitation": "exploits",
    "CapabilityInvolvement": "involves",
    "EntityOperationalCapabilityInvolvement": "involves",
    "MissionInvolvement": "involves",
}
"""A map that for relabelling specific ModelObject types."""


def exchange_items(obj: m.ModelElement) -> str:
    """Return ``obj``'s ``ExchangeItem``s names.

    The returned string is wrapped in [E1,...] and separated by ','.
    """
    assert isinstance(obj, fa.FunctionalExchange | fa.ComponentExchange)
    if items := ", ".join(item.name for item in obj.exchange_items):
        return f"[{items}]"
    return ""


def exchange_name_and_items(
    obj: m.ModelElement, label: str | None = None
) -> str:
    """Return ``obj``'s name and ``ExchangeItem``s if there are any."""
    label = label or obj.name
    if ex_items := exchange_items(obj):
        label += " " + ex_items
    return label


def uuid_filter(obj: m.ModelElement, label: str | None = None) -> str:
    """Return ``obj``'s name or ``obj`` if string w/o UUIDs in it."""
    filtered_label = label if label is not None else obj.name
    assert isinstance(filtered_label, str)
    return UUID_PTRN.sub("", filtered_label)


def relabel_system_exchange(obj: m.ModelElement, label: str | None) -> str:
    """Return converted label from ``obj``, a system exchanges."""
    label_map = LABEL_CONVERSION
    if patch := label_map.get(type(obj).__name__):
        return f"« {patch} »"
    return label or obj.name


FILTER_LABEL_ADJUSTERS: dict[
    str, cabc.Callable[[m.ModelElement, str | None], str]
] = {
    EX_ITEMS: lambda obj, _: exchange_items(obj),
    SHOW_EX_ITEMS: exchange_name_and_items,
    EX_ITEMS_OR_EXCH: lambda obj, label: (
        exchange_items(obj)
        if getattr(obj, "exchange_items", "")
        else label or obj.name
    ),
    NO_UUID: uuid_filter,
    SYSTEM_EX_RELABEL: relabel_system_exchange,
}
"""Label adjuster registry."""


def sort_exchange_items_label(
    value: bool,
    exchange: m.ModelElement,
    adjustments: dict[str, t.Any],
) -> None:
    """Sort the exchange items in the exchange label if value is true."""
    items = [item.name for item in exchange.exchange_items]
    if value:
        items = sorted(items)
    adjustments["labels_text"] = ", ".join(items)


RENDER_ADJUSTERS: dict[
    str, cabc.Callable[[bool, m.ModelElement, dict[str, t.Any]], None]
] = {"sorted_exchangedItems": sort_exchange_items_label}
"""Available custom render parameter-solvers registry."""
