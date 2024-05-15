# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""
Collection of [`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
on diagrams that involve ports.
"""
from __future__ import annotations

import collections.abc as cabc
import typing as t
from itertools import chain

from capellambse import helpers
from capellambse.model import common
from capellambse.model.crosslayer import cs, fa
from capellambse.model.layers import ctx as sa
from capellambse.model.layers import la
from capellambse.model.modeltypes import DiagramType as DT

from .. import _elkjs
from . import exchanges, generic, makers

if t.TYPE_CHECKING:
    from .. import context

    DerivatorFunction: t.TypeAlias = cabc.Callable[
        [context.ContextDiagram, _elkjs.ELKInputData, _elkjs.ELKInputChild],
        None,
    ]

STYLECLASS_PREFIX = "__Derived"


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    diagram.display_derived_interfaces = (params or {}).pop(
        "display_derived_interfaces", diagram.display_derived_interfaces
    )
    data = generic.collector(diagram, no_symbol=True)
    ports = port_collector(diagram.target, diagram.type)
    centerbox = data["children"][0]
    connections = port_exchange_collector(ports)
    centerbox["ports"] = [
        makers.make_port(uuid) for uuid, edges in connections.items() if edges
    ]
    ex_datas: list[generic.ExchangeData] = []
    edges: common.ElementList[fa.AbstractExchange] = list(
        chain.from_iterable(connections.values())
    )
    for ex in edges:
        if is_hierarchical := exchanges.is_hierarchical(ex, centerbox):
            if not diagram.display_parent_relation:
                continue
            centerbox["labels"][0][
                "layoutOptions"
            ] = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
            elkdata: _elkjs.ELKInputData = centerbox
        else:
            elkdata = data
        try:
            ex_data = generic.ExchangeData(
                ex, elkdata, diagram.filters, params, is_hierarchical
            )
            generic.exchange_data_collector(ex_data)
            ex_datas.append(ex_data)
        except AttributeError:
            continue
    global_boxes = {centerbox["id"]: centerbox}
    made_boxes = {centerbox["id"]: centerbox}
    boxes_to_delete = {centerbox["id"]}

    def _make_box_and_update_globals(
        obj: t.Any,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        box = makers.make_box(
            obj,
            **kwargs,
        )
        global_boxes[obj.uuid] = box
        made_boxes[obj.uuid] = box
        return box

    def _make_owner_box(current: t.Any) -> t.Any:
        if not (parent_box := global_boxes.get(current.owner.uuid)):
            parent_box = _make_box_and_update_globals(
                current.owner,
                no_symbol=diagram.display_symbols_as_boxes,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
        for box in (children := parent_box.setdefault("children", [])):
            if box["id"] == current.uuid:
                box = global_boxes.get(current.uuid, current)
                break
        else:
            children.append(global_boxes.get(current.uuid, current))
        boxes_to_delete.add(current.uuid)
        return current.owner

    if diagram.display_parent_relation:
        try:
            if not isinstance(diagram.target.owner, generic.PackageTypes):
                box = _make_box_and_update_globals(
                    diagram.target.owner,
                    no_symbol=diagram.display_symbols_as_boxes,
                    layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
                )
                box["children"] = [centerbox]
                del data["children"][0]
        except AttributeError:
            pass
        diagram_target_owners = generic.get_all_owners(diagram.target)
        common_owners = set()

    stack_heights: dict[str, float | int] = {
        "input": -makers.NEIGHBOR_VMARGIN,
        "output": -makers.NEIGHBOR_VMARGIN,
    }
    for child, local_ports, side in port_context_collector(ex_datas, ports):
        _, label_height = helpers.get_text_extent(child.name)
        height = max(
            label_height + 2 * makers.LABEL_VPAD,
            makers.PORT_PADDING
            + (makers.PORT_SIZE + makers.PORT_PADDING) * len(local_ports),
        )
        if box := global_boxes.get(child.uuid):  # type: ignore[assignment]
            if box is centerbox:
                continue
            box.setdefault("ports", []).extend(
                [makers.make_port(j.uuid) for j in local_ports]
            )
            box["height"] += height
        else:
            box = _make_box_and_update_globals(
                child,
                height=height,
                no_symbol=diagram.display_symbols_as_boxes,
            )
            box["ports"] = [makers.make_port(j.uuid) for j in local_ports]

        if diagram.display_parent_relation:
            current = child
            while current and current.uuid not in diagram_target_owners:
                try:
                    if isinstance(current.owner, generic.PackageTypes):
                        break
                    current = _make_owner_box(current)
                except AttributeError:
                    break
            common_owners.add(current.uuid)

        stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    if diagram.display_parent_relation and diagram.target.owner:
        current = diagram.target.owner
        common_owner_uuid = current.uuid
        for owner in diagram_target_owners[::-1]:
            if owner in common_owners:
                common_owner_uuid = owner
                break
        while current and current.uuid != common_owner_uuid:
            try:
                if isinstance(current.owner, generic.PackageTypes):
                    break
                current = _make_owner_box(current)
            except AttributeError:
                break

    for uuid in boxes_to_delete:
        del global_boxes[uuid]
    data["children"].extend(global_boxes.values())
    if diagram.display_parent_relation:
        owner_boxes: dict[str, _elkjs.ELKInputChild] = {
            uuid: box
            for uuid, box in made_boxes.items()
            if box.get("children")
        }
        generic.move_parent_boxes_to_owner(owner_boxes, diagram.target, data)
        generic.move_edges(owner_boxes, edges, data)

    centerbox["height"] = max(centerbox["height"], *stack_heights.values())
    derivator = DERIVATORS.get(type(diagram.target))
    if diagram.display_derived_interfaces and derivator is not None:
        derivator(diagram, data, made_boxes[diagram.target.uuid])

    return data


def port_collector(
    target: common.GenericElement | common.ElementList, diagram_type: DT
) -> list[common.GenericElement]:
    """Savely collect ports from `target`."""

    def __collect(target):
        all_ports: list[common.GenericElement] = []
        for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram_type]:
            try:
                ports = getattr(target, attr)
                if ports and isinstance(
                    ports[0],
                    (fa.FunctionPort, fa.ComponentPort, cs.PhysicalPort),
                ):
                    all_ports.extend(ports)
            except AttributeError:
                pass
        return all_ports

    if isinstance(target, cabc.Iterable):
        assert not isinstance(target, common.GenericElement)
        all_ports: list[common.GenericElement] = []
        for obj in target:
            all_ports.extend(__collect(obj))
    else:
        all_ports = __collect(target)
    return all_ports


def port_exchange_collector(
    ports: t.Iterable[common.GenericElement],
    filter: cabc.Callable[
        [cabc.Iterable[common.GenericElement]],
        cabc.Iterable[common.GenericElement],
    ] = lambda i: i,
) -> dict[str, common.ElementList[fa.AbstractExchange]]:
    """Collect exchanges from `ports` savely."""
    edges: dict[str, common.ElementList[fa.AbstractExchange]] = {}
    for i in ports:
        try:
            edges[i.uuid] = filter(getattr(i, "exchanges"))
        except AttributeError:
            pass
    return edges


class ContextInfo(t.NamedTuple):
    """ContextInfo data."""

    element: common.GenericElement
    """An element of context."""
    ports: list[common.GenericElement]
    """The context element's relevant ports.

    This list only contains ports that at least one of the exchanges
    passed into ``collect_exchanges`` sees.
    """
    side: t.Literal["input", "output"]
    """Whether this is an input or output to the element of interest."""


def port_context_collector(
    exchange_datas: t.Iterable[generic.ExchangeData],
    local_ports: t.Container[common.GenericElement],
) -> t.Iterator[ContextInfo]:
    """Collect the context objects.

    Parameters
    ----------
    exchange_datas
        The ``ExchangeData``s to look at to find new elements.
    local_ports
        Connectors/Ports lookup where ``exchange_datas`` is checked
        against. If an exchange connects via a port from ``local_ports``
        it is collected.

    Returns
    -------
    contexts
        An iterator over
        [`ContextDiagram.ContextInfo`s][capellambse_context_diagrams.context.ContextDiagram].
    """

    ctx: dict[str, ContextInfo] = {}
    side: t.Literal["input", "output"]
    for exd in exchange_datas:
        try:
            source, target = generic.collect_exchange_endpoints(exd)
        except AttributeError:
            continue

        if source in local_ports:
            port = target
            side = "output"
        elif target in local_ports:
            port = source
            side = "input"
        else:
            continue

        try:
            owner = port.owner  # type: ignore[attr-defined]
        except AttributeError:
            continue

        info = ContextInfo(owner, [], side)
        info = ctx.setdefault(owner.uuid, info)
        if port not in info.ports:
            info.ports.append(port)

    return iter(ctx.values())


def derive_from_functions(
    diagram: context.ContextDiagram,
    data: _elkjs.ELKInputData,
    centerbox: _elkjs.ELKInputChild,
) -> None:
    """Derive Components from allocated functions of the context target.

    A Component, a ComponentExchange and two ComponentPorts are added
    to ``data``. These elements are prefixed with ``Derived-`` to
    receive special styling in the serialization step.
    """
    assert isinstance(diagram.target, cs.Component)
    ports = []
    for fnc in diagram.target.allocated_functions:
        ports.extend(port_collector(fnc, diagram.type))

    context_box_ids = {child["id"] for child in data["children"]}
    components: dict[str, cs.Component] = {}
    for port in ports:
        for fex in port.exchanges:
            if isinstance(port, fa.FunctionOutputPort):
                attr = "target"
            else:
                attr = "source"

            try:
                derived_comp = getattr(fex, attr).owner.owner
                if (
                    derived_comp == diagram.target
                    or derived_comp.uuid in context_box_ids
                ):
                    continue

                if derived_comp.uuid not in components:
                    components[derived_comp.uuid] = derived_comp
            except AttributeError:  # No owner of owner.
                pass

    # Idea: Include flow direction of derived interfaces from all functional
    # exchanges. Mixed means bidirectional. Just even out bidirectional
    # interfaces and keep flow direction of others.

    for i, (uuid, derived_component) in enumerate(components.items(), 1):
        box = makers.make_box(
            derived_component,
            no_symbol=diagram.display_symbols_as_boxes,
        )
        class_ = type(derived_comp).__name__
        box["id"] = f"{STYLECLASS_PREFIX}-{class_}:{uuid}"
        data["children"].append(box)
        source_id = f"{STYLECLASS_PREFIX}-CP_INOUT:{i}"
        target_id = f"{STYLECLASS_PREFIX}-CP_INOUT:{-i}"
        box.setdefault("ports", []).append(makers.make_port(source_id))
        centerbox.setdefault("ports", []).append(makers.make_port(target_id))
        if i % 2 == 0:
            source_id, target_id = target_id, source_id

        data["edges"].append(
            {
                "id": f"{STYLECLASS_PREFIX}-ComponentExchange:{i}",
                "sources": [source_id],
                "targets": [target_id],
            }
        )

    data["children"][0]["height"] += (
        makers.PORT_PADDING
        + (makers.PORT_SIZE + makers.PORT_PADDING) * len(components) // 2
    )


DERIVATORS: dict[type[common.GenericElement], DerivatorFunction] = {
    la.LogicalComponent: derive_from_functions,
    sa.SystemComponent: derive_from_functions,
}
"""Supported objects to build derived contexts for."""
