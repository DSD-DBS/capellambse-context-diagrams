# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functionality for collecting model data.

The data stems from an instance of
[`MelodyModel`][capellambse.model.MelodyModel] and converts it into
[`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""

from __future__ import annotations

import collections.abc as cabc
import logging
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa, interaction
from capellambse.model import DiagramType as DT

from .. import _elkjs, context, filters
from ..builders import _makers

if t.TYPE_CHECKING:
    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]

logger = logging.getLogger(__name__)

SourceAndTarget = tuple[m.ModelElement, m.ModelElement]

PHYSICAL_CONNECTOR_ATTR_NAMES = ("physical_ports",)
"""Attribute of PhysicalComponents for receiving connections."""
CONNECTOR_ATTR_NAMES = ("ports", "inputs", "outputs")
"""Attribute of ModelElements for receiving connections."""
DIAGRAM_TYPE_TO_CONNECTOR_NAMES: dict[DT, tuple[str, ...]] = {
    DT.OAB: (),
    DT.OAIB: (),
    DT.OCB: (),
    DT.MCB: (),
    DT.SAB: CONNECTOR_ATTR_NAMES,
    DT.SDFB: CONNECTOR_ATTR_NAMES,
    DT.LAB: CONNECTOR_ATTR_NAMES,
    DT.LDFB: CONNECTOR_ATTR_NAMES,
    DT.PAB: CONNECTOR_ATTR_NAMES + PHYSICAL_CONNECTOR_ATTR_NAMES,
    DT.PDFB: CONNECTOR_ATTR_NAMES + PHYSICAL_CONNECTOR_ATTR_NAMES,
}
"""Supported diagram types mapping to the attribute name of connectors."""
MARKER_SIZE = 3
"""Default size of marker-ends in pixels."""
MARKER_PADDING = _makers.PORT_PADDING
"""Default padding of markers in pixels."""


def collector(
    diagram: context.ContextDiagram,
    *,
    width: int | float = _makers.EOI_WIDTH,
    no_symbol: bool = False,
) -> _elkjs.ELKInputData:
    """Return ELK data with only centerbox in children and config."""
    data = _makers.make_diagram(diagram)
    data.children = [
        _makers.make_box(
            diagram.target,
            width=width,
            no_symbol=no_symbol,
            slim_width=diagram._slim_center_box,
        )
    ]
    return data


def collect_exchange_endpoints(
    ex: ExchangeData | m.ModelElement,
) -> SourceAndTarget:
    """Safely collect exchange endpoints from ``ex``."""
    if isinstance(ex, ExchangeData):
        if ex.is_hierarchical:
            return ex.exchange.target, ex.exchange.source
        return ex.exchange.source, ex.exchange.target
    return ex.source, ex.target


class ExchangeData(t.NamedTuple):
    """Exchange data for ELK."""

    exchange: m.ModelElement
    """An exchange from the capellambse model."""
    elkdata: _elkjs.ELKInputData
    """The collected elkdata to add the edges in there."""
    filter_iterable: cabc.Iterable[str]
    """A string that maps to a filter label adjuster callable in
    [`FILTER_LABEL_ADJUSTERS`][capellambse_context_diagrams.filters.FILTER_LABEL_ADJUSTERS].
    """
    params: dict[str, t.Any] | None = None
    """Optional dictionary of additional render params."""
    is_hierarchical: bool = False
    """True if exchange isn't global, i.e. nested inside a box."""


def exchange_data_collector(
    data: ExchangeData,
    endpoint_collector: cabc.Callable[
        [m.ModelElement], SourceAndTarget
    ] = collect_exchange_endpoints,
) -> SourceAndTarget:
    """Return source and target port from `exchange`.

    Additionally inflate `elkdata.children` with input data for ELK.
    You can handover a filter name that corresponds to capellambse
    filters. This will apply filter functionality from
    [`filters.FILTER_LABEL_ADJUSTERS`][capellambse_context_diagrams.filters.FILTER_LABEL_ADJUSTERS].

    Parameters
    ----------
    data
        Instance of [`ExchangeData`][capellambse_context_diagrams.collectors._generic.ExchangeData]
        storing all needed elements for collection.
    endpoint_collector
        Optional collector function for Exchange endpoints. Defaults to
        [`collect_exchange_endpoints`][capellambse_context_diagrams.collectors._generic.collect_exchange_endpoints].

    Returns
    -------
    source, target
        A tuple consisting of the exchange's source and target elements.
    """
    source, target = endpoint_collector(data.exchange)
    if data.is_hierarchical:
        target, source = source, target

    params = (data.params or {}).copy()
    # Remove simple render parameters from params
    no_edgelabels: bool = params.pop("no_edgelabels", False)
    params.pop("transparent_background", False)
    _ = params.pop("font_family", "Open Sans")
    _ = params.pop("font_size", 12)

    render_adj: dict[str, t.Any] = {}
    for name, value in params.items():
        try:
            filters.RENDER_ADJUSTERS[name](value, data.exchange, render_adj)
        except KeyError:
            logger.exception(
                "There is no render parameter solver labelled: '%s' "
                "in filters.RENDER_ADJUSTERS",
                name,
            )

    data.elkdata.edges.append(
        _elkjs.ELKInputEdge(
            id=render_adj.get("id", data.exchange.uuid),
            sources=[render_adj.get("sources", source.uuid)],
            targets=[render_adj.get("targets", target.uuid)],
        )
    )

    label = collect_label(data.exchange)
    for filter in data.filter_iterable:
        try:
            label = filters.FILTER_LABEL_ADJUSTERS[filter](
                data.exchange, label
            )
        except KeyError:
            logger.exception(
                "There is no filter labelled: '%s' in "
                "filters.FILTER_LABEL_ADJUSTERS",
                filter,
            )

    if label and not no_edgelabels:
        data.elkdata.edges[-1].labels = _makers.make_label(
            render_adj.get("labels_text", label),
            max_width=_makers.MAX_LABEL_WIDTH,
        )

    return source, target


def collect_label(obj: m.ModelElement) -> str | None:
    """Return the label of a given object.

    The label usually comes from the `.name` attribute. Special handling
    for [`interaction.AbstractCapabilityExtend`][capellambse.metamodel.interaction.AbstractCapabilityExtend]
    and [interaction.AbstractCapabilityInclude`][capellambse.metamodel.interaction.AbstractCapabilityInclude].
    """
    if isinstance(obj, interaction.AbstractCapabilityExtend):
        return "« e »"
    if isinstance(obj, interaction.AbstractCapabilityInclude):
        return "« i »"
    return "" if obj.name.startswith("(Unnamed") else obj.name


def move_edges(
    boxes: cabc.Mapping[str, _elkjs.ELKInputChild],
    connections: cabc.Iterable[m.ModelElement],
    data: _elkjs.ELKInputData,
    portless: bool = False,
) -> None:
    """Move edges to boxes."""
    edges_to_remove: list[str] = []
    for c in connections:
        source_owner_uuids = list(get_all_owners(c.source))
        target_owner_uuids = list(get_all_owners(c.target))
        if c.source == c.target:
            source_owner_uuids.remove(c.source.uuid)
            target_owner_uuids.remove(c.source.uuid)

        if c.source.owner is not None and c.target.owner is not None:
            cycle_detected = c.source.owner.uuid == c.target.owner.uuid
        else:
            cycle_detected = False

        common_owner_uuid = None
        for owner in source_owner_uuids:
            if owner in target_owner_uuids:
                common_owner_uuid = owner
                if cycle_detected and not portless:
                    cycle_detected = False
                else:
                    break

        if not common_owner_uuid or not (
            owner_box := boxes.get(common_owner_uuid)
        ):
            continue

        for edge in data.edges:
            if edge.id == c.uuid:
                owner_box.edges.append(edge)
                edges_to_remove.append(edge.id)

    data.edges = [e for e in data.edges if e.id not in edges_to_remove]


def get_all_owners(obj: m.ModelElement) -> cabc.Iterator[str]:
    """Return the UUIDs from all owners of ``obj``."""
    current: m.ModelElement | None = obj
    while current is not None:
        yield current.uuid
        current = getattr(current, "owner", None)


def port_collector(
    target: m.ModelElement | m.ElementList, diagram_type: DT
) -> tuple[dict[str, m.ModelElement], dict[str, m.ModelElement]]:
    """Collect ports from `target` savely."""

    def __collect(target):
        port_types = fa.FunctionPort | fa.ComponentPort | cs.PhysicalPort
        incoming_ports: dict[str, m.ModelElement] = {}
        outgoing_ports: dict[str, m.ModelElement] = {}
        for attr in DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram_type]:
            try:
                ports = getattr(target, attr)
                if not ports or not isinstance(ports[0], port_types):
                    continue

                if attr == "inputs":
                    incoming_ports.update({p.uuid: p for p in ports})
                elif attr == "ports":
                    for port in ports:
                        if port.direction == "IN":
                            incoming_ports[port.uuid] = port
                        else:
                            outgoing_ports[port.uuid] = port
                else:
                    outgoing_ports.update({p.uuid: p for p in ports})
            except AttributeError:
                pass
        return incoming_ports, outgoing_ports

    if isinstance(target, cabc.Iterable):
        assert not isinstance(target, m.ModelElement)
        incoming_ports: dict[str, m.ModelElement] = {}
        outgoing_ports: dict[str, m.ModelElement] = {}
        for obj in target:
            inc, out = __collect(obj)
            incoming_ports.update(inc)
            outgoing_ports.update(out)
    else:
        incoming_ports, outgoing_ports = __collect(target)
    return incoming_ports, outgoing_ports


def _extract_edges(
    obj: m.ModelElement,
    attribute: str,
    filter: Filter,
) -> cabc.Iterable[m.ModelElement]:
    return filter(getattr(obj, attribute, []))


def port_exchange_collector(
    ports: t.Iterable[m.ModelElement],
    filter: Filter = lambda i: i,
) -> dict[str, list[fa.AbstractExchange]]:
    """Collect exchanges from `ports` savely."""
    edges: dict[str, list[fa.AbstractExchange]] = {}

    for port in ports:
        if exs := _extract_edges(port, "exchanges", filter):
            edges[port.uuid] = t.cast(list[fa.AbstractExchange], exs)
            continue

        if links := _extract_edges(port, "links", filter):
            edges[port.uuid] = t.cast(list[fa.AbstractExchange], links)

    return edges
