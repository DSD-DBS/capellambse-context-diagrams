# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
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
from capellambse.metamodel import interaction, la, oa, pa, sa
from capellambse.model import DiagramType as DT

from .. import _elkjs, context, filters
from . import makers

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
MARKER_PADDING = makers.PORT_PADDING
"""Default padding of markers in pixels."""
PackageTypes: tuple[type[m.ModelElement], ...] = (
    oa.EntityPkg,
    la.LogicalComponentPkg,
    sa.SystemComponentPkg,
    pa.PhysicalComponentPkg,
)


def collector(
    diagram: context.ContextDiagram,
    *,
    width: int | float = makers.EOI_WIDTH,
    no_symbol: bool = False,
) -> _elkjs.ELKInputData:
    """Return ELK data with only centerbox in children and config."""
    data = makers.make_diagram(diagram)
    data.children = [
        makers.make_box(
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
        data.elkdata.edges[-1].labels = makers.make_label(
            render_adj.get("labels_text", label),
            max_width=makers.MAX_LABEL_WIDTH,
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


def move_parent_boxes_to_owner(
    boxes: dict[str, _elkjs.ELKInputChild],
    obj: m.ModelElement,
    data: _elkjs.ELKInputData,
    filter_types: tuple[type, ...] = PackageTypes,
) -> None:
    """Move boxes to their owner box."""
    boxes_to_remove: list[str] = []
    for child in data.children:
        if not child.children:
            continue

        owner = obj._model.by_uuid(child.id)
        if (
            isinstance(owner, filter_types)
            or not (oowner := owner.owner)
            or isinstance(oowner, filter_types)
            or not (oowner_box := boxes.get(oowner.uuid))
        ):
            continue

        oowner_box.children.append(child)
        boxes_to_remove.append(child.id)

    data.children = [b for b in data.children if b.id not in boxes_to_remove]


def move_edges(
    boxes: cabc.Mapping[str, _elkjs.ELKInputChild],
    connections: cabc.Iterable[m.ModelElement],
    data: _elkjs.ELKInputData,
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
                if cycle_detected:
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


def make_owner_box(
    obj: t.Any,
    make_box_func: t.Callable,
    boxes: dict[str, _elkjs.ELKInputChild],
    boxes_to_delete: set[str],
) -> t.Any:
    parent_box = make_box_func(
        obj.owner,
        layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
    )
    assert (obj_box := boxes.get(obj.uuid))
    for box in (children := parent_box.children):
        if box.id == obj.uuid:
            break
    else:
        children.append(obj_box)
        obj_box.width = max(
            obj_box.width,
            parent_box.width,
        )
        for label in parent_box.labels:
            label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
    boxes_to_delete.add(obj.uuid)
    return obj.owner


def make_owner_boxes(
    obj: m.ModelElement,
    excluded: list[str],
    make_box_func: t.Callable,
    boxes: dict[str, _elkjs.ELKInputChild],
    boxes_to_delete: set[str],
) -> str:
    """Create owner boxes for all owners of ``obj``."""
    current = obj
    while (
        current
        and current.uuid not in excluded
        and getattr(current, "owner", None) is not None
        and not isinstance(current.owner, PackageTypes)
    ):
        current = make_owner_box(
            current, make_box_func, boxes, boxes_to_delete
        )
    return current.uuid
