# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""
Functionality for collection of model data from an instance of [`MelodyModel`][capellambse.model.MelodyModel]
and conversion of it into [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""

from __future__ import annotations

import collections.abc as cabc
import logging
import typing as t

from capellambse import helpers
from capellambse.model import common
from capellambse.model.crosslayer import interaction
from capellambse.model.modeltypes import DiagramType as DT

from .. import _elkjs, context, filters
from . import makers

logger = logging.getLogger(__name__)

SourceAndTarget = tuple[common.GenericElement, common.GenericElement]


CONNECTOR_ATTR_NAMES = {"inputs", "outputs", "physical_ports"}
"""Attribute of GenericElements for receiving connections."""
PORTLESS_DIAGRAM_TYPES = {DT.OAB, DT.OAIB, DT.OCB, DT.MCB}
"""Supported diagram types without connectors (i.e. ports)."""
MARKER_SIZE = 3
"""Default size of marker-ends in pixels."""
MARKER_PADDING = makers.PORT_PADDING
"""Default padding of markers in pixels."""


def collector(
    diagram: context.ContextDiagram,
    *,
    width: int | float = makers.EOI_WIDTH,
    no_symbol: bool = False,
) -> _elkjs.ELKInputData:
    """Returns ``ELKInputData`` with only centerbox in children and config."""
    data = makers.make_diagram(diagram)
    data["children"] = [
        makers.make_box(diagram.target, width=width, no_symbol=no_symbol)
    ]
    return data


def collect_exchange_endpoints(
    e: common.GenericElement,
) -> tuple[common.GenericElement, common.GenericElement]:
    """Safely collect exchange endpoints from `e`."""
    return e.source, e.target


class ExchangeData(t.NamedTuple):
    """Exchange data for ELK."""

    exchange: common.GenericElement
    """An exchange from the capellambse model."""
    elkdata: _elkjs.ELKInputData
    """The collected elkdata to add the edges in there."""
    filter_iterable: cabc.Iterable[str]
    """
    A string that maps to a filter label adjuster
    callable in
    [`FILTER_LABEL_ADJUSTERS`][capellambse_context_diagrams.filters.FILTER_LABEL_ADJUSTERS].
    """
    params: dict[str, t.Any] | None = None
    """Optional dictionary of additional render params."""


def exchange_data_collector(
    data: ExchangeData,
    endpoint_collector: cabc.Callable[
        [common.GenericElement], SourceAndTarget
    ] = collect_exchange_endpoints,
) -> tuple[common.GenericElement, common.GenericElement]:
    """Return source and target port from `exchange`.

    Additionally inflate `elkdata["children"]` with input data for ELK.
    You can handover a filter name that corresponds to capellambse
    filters. This will apply filter functionality from
    [`filters.FILTER_LABEL_ADJUSTERS`][capellambse_context_diagrams.filters.FILTER_LABEL_ADJUSTERS].

    Parameters
    ----------
    data
        Instance of [`ExchangeData`][capellambse_context_diagrams.collectors.generic.ExchangeData]
        storing all needed elements for collection.
    endpoint_collector
        Optional collector function for Exchange endpoints. Defaults to
        [`collect_exchange_endpoints`][capellambse_context_diagrams.collectors.generic.collect_exchange_endpoints].

    Returns
    -------
    source, target
        A tuple consisting of the exchange's source and target elements.
    """
    source, target = endpoint_collector(data.exchange)
    label = collect_label(data.exchange)
    for filter in data.filter_iterable:
        try:
            label = filters.FILTER_LABEL_ADJUSTERS[filter](
                data.exchange, label
            )
        except KeyError:
            logger.exception(
                "There is no filter labelled: '%s' in filters.FILTER_LABEL_ADJUSTERS",
                filter,
            )

    params = (data.params or {}).copy()
    # Remove simple render parameters from params
    no_edgelabels: bool = params.pop("no_edgelabels", False)

    render_adj: dict[str, t.Any] = {}
    for name, value in params.items():
        try:
            filters.RENDER_ADJUSTERS[name](value, data.exchange, render_adj)
        except KeyError:
            logger.exception(
                "There is no render parameter solver labelled: '%s' in filters.RENDER_ADJUSTERS",
                name,
            )

    data.elkdata["edges"].append(
        {
            "id": render_adj.get("id", data.exchange.uuid),
            "sources": [render_adj.get("sources", source.uuid)],
            "targets": [render_adj.get("targets", target.uuid)],
        },
    )
    if label and not no_edgelabels:
        width, height = helpers.extent_func(label)
        data.elkdata["edges"][-1]["labels"] = [
            {
                "text": render_adj.get("labels_text", label),
                "width": render_adj.get(
                    "labels_width", width + 2 * makers.LABEL_HPAD
                ),
                "height": render_adj.get(
                    "labels_height", height + 2 * makers.LABEL_VPAD
                ),
            }
        ]

    return source, target


def collect_label(obj: common.GenericElement) -> str | None:
    """Return the label of a given object.

    The label usually comes from the `.name` attribute. Special handling
    for [`interaction.AbstractCapabilityExtend`][capellambse.model.crosslayer.interaction.AbstractCapabilityExtend]
    and [interaction.AbstractCapabilityInclude`][capellambse.model.crosslayer.interaction.AbstractCapabilityInclude].
    """
    if isinstance(obj, interaction.AbstractCapabilityExtend):
        return "« e »"
    elif isinstance(obj, interaction.AbstractCapabilityInclude):
        return "« i »"
    return "" if obj.name.startswith("(Unnamed") else obj.name
