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

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[common.GenericElement]],
        cabc.Iterable[common.GenericElement],
    ]


class ContextProcessor:
    def __init__(
        self,
        diagram: context.ContextDiagram,
        data: _elkjs.ELKInputData,
        *,
        params: dict[str, t.Any] | None = None,
    ) -> None:
        self.diagram = diagram
        self.data = data
        self.params = params or {}
        self.centerbox = self.data.children[0]
        self.global_boxes = {self.centerbox.id: self.centerbox}
        self.made_boxes = {self.centerbox.id: self.centerbox}
        self.boxes_to_delete = {self.centerbox.id}
        self.edges: list[fa.AbstractExchange] = []
        if self.diagram._display_parent_relation:
            self.diagram_target_owners = list(
                generic.get_all_owners(self.diagram.target)
            )
            self.common_owners: set[str] = set()

    def process_context(self):
        if (
            self.diagram._display_parent_relation
            and getattr(self.diagram.target, "owner", None) is not None
            and not isinstance(self.diagram.target.owner, generic.PackageTypes)
        ):
            box = self._make_box(
                self.diagram.target.owner,
                no_symbol=self.diagram._display_symbols_as_boxes,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
            box.children = [self.centerbox]
            del self.data.children[0]

        stack_heights: dict[str, float | int] = {
            "input": -makers.NEIGHBOR_VMARGIN,
            "output": -makers.NEIGHBOR_VMARGIN,
        }
        self._process_ports(stack_heights)

        if self.diagram._display_parent_relation and self.diagram.target.owner:
            current = self.diagram.target.owner
            while (
                current
                and self.common_owners
                and hasattr(current, "owner")
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                current = self._make_owner_box(
                    self.diagram,
                    current,
                )
                self.common_owners.discard(current.uuid)

        for uuid in self.boxes_to_delete:
            del self.global_boxes[uuid]

        self.data.children.extend(self.global_boxes.values())
        if self.diagram._display_parent_relation:
            owner_boxes: dict[str, _elkjs.ELKInputChild] = {
                uuid: box
                for uuid, box in self.made_boxes.items()
                if box.children
            }
            generic.move_parent_boxes_to_owner(
                owner_boxes, self.diagram.target, self.data
            )
            generic.move_edges(owner_boxes, self.edges, self.data)

        self.centerbox.height = max(
            self.centerbox.height, *stack_heights.values()
        )

    def _process_exchanges(self) -> tuple[
        list[common.GenericElement],
        list[generic.ExchangeData],
    ]:
        ports = port_collector(self.diagram.target, self.diagram.type)
        connections = port_exchange_collector(ports)
        self.centerbox.ports = [makers.make_port(uuid) for uuid in connections]
        self.edges = list(chain.from_iterable(connections.values()))
        ex_datas: list[generic.ExchangeData] = []
        for ex in self.edges:
            if is_hierarchical := exchanges.is_hierarchical(
                ex, self.centerbox
            ):
                if not self.diagram._display_parent_relation:
                    continue
                self.centerbox.labels[0].layoutOptions = (
                    makers.DEFAULT_LABEL_LAYOUT_OPTIONS
                )
                elkdata: _elkjs.ELKInputData = self.centerbox
            else:
                elkdata = self.data
            try:
                ex_data = generic.ExchangeData(
                    ex,
                    elkdata,
                    self.diagram.filters,
                    self.params,
                    is_hierarchical,
                )
                generic.exchange_data_collector(ex_data)
                ex_datas.append(ex_data)
            except AttributeError:
                continue

        return ports, ex_datas

    def _process_ports(self, stack_heights: dict[str, float | int]) -> None:
        ports, ex_datas = self._process_exchanges()
        for port, local_ports, side in port_context_collector(ex_datas, ports):
            _, label_height = helpers.get_text_extent(port.name)
            height = max(
                label_height + 2 * makers.LABEL_VPAD,
                makers.PORT_PADDING
                + (makers.PORT_SIZE + makers.PORT_PADDING) * len(local_ports),
            )
            if box := self.global_boxes.get(port.uuid):  # type: ignore[assignment]
                if box is self.centerbox:
                    continue
                box.ports.extend(
                    [makers.make_port(j.uuid) for j in local_ports]
                )
                box.height += height
            else:
                box = self._make_box(
                    port,
                    height=height,
                    no_symbol=self.diagram._display_symbols_as_boxes,
                )
                box.ports = [makers.make_port(j.uuid) for j in local_ports]

            if self.diagram._display_parent_relation:
                current = port
                while (
                    current
                    and current.uuid not in self.diagram_target_owners
                    and getattr(current, "owner", None) is not None
                    and not isinstance(current.owner, generic.PackageTypes)
                ):
                    current = self._make_owner_box(self.diagram, current)
                self.common_owners.add(current.uuid)

            stack_heights[side] += makers.NEIGHBOR_VMARGIN + height

    def _make_box(
        self,
        obj: t.Any,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        box = makers.make_box(
            obj,
            **kwargs,
        )
        self.global_boxes[obj.uuid] = box
        self.made_boxes[obj.uuid] = box
        return box

    def _make_owner_box(
        self,
        diagram: context.ContextDiagram,
        obj: t.Any,
    ) -> t.Any:
        if not (parent_box := self.global_boxes.get(obj.owner.uuid)):
            parent_box = self._make_box(
                obj.owner,
                no_symbol=diagram._display_symbols_as_boxes,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
        assert (obj_box := self.global_boxes.get(obj.uuid))
        for box in (children := parent_box.children):
            if box.id == obj.uuid:
                box = obj_box
                break
        else:
            children.append(obj_box)
        self.boxes_to_delete.add(obj.uuid)
        return obj.owner


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    data = generic.collector(diagram, no_symbol=True)
    processor = ContextProcessor(diagram, data, params=params)
    processor.process_context()
    derivator = DERIVATORS.get(type(diagram.target))
    if diagram._display_derived_interfaces and derivator is not None:
        derivator(
            diagram,
            data,
            processor.made_boxes[diagram.target.uuid],
        )
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


def _extract_edges(
    obj: common.ElementList[common.GenericElement],
    attribute: str,
    filter: Filter,
) -> common.ElementList[common.GenericElement] | list:
    return filter(getattr(obj, attribute, []))


def port_exchange_collector(
    ports: t.Iterable[common.GenericElement],
    filter: Filter = lambda i: i,
) -> dict[str, common.ElementList[fa.AbstractExchange]]:
    """Collect exchanges from `ports` savely."""
    edges: dict[str, common.ElementList[fa.AbstractExchange]] = {}

    for port in ports:
        if exs := _extract_edges(port, "exchanges", filter):
            edges[port.uuid] = exs
            continue

        if links := _extract_edges(port, "links", filter):
            edges[port.uuid] = links

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

    context_box_ids = {child.id for child in data.children}
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
            no_symbol=diagram._display_symbols_as_boxes,
        )
        class_ = type(derived_comp).__name__
        box.id = f"{makers.STYLECLASS_PREFIX}-{class_}:{uuid}"
        data.children.append(box)
        source_id = f"{makers.STYLECLASS_PREFIX}-CP_INOUT:{i}"
        target_id = f"{makers.STYLECLASS_PREFIX}-CP_INOUT:{-i}"
        box.ports.append(makers.make_port(source_id))
        centerbox.ports.append(makers.make_port(target_id))
        if i % 2 == 0:
            source_id, target_id = target_id, source_id

        data.edges.append(
            _elkjs.ELKInputEdge(
                id=f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{i}",
                sources=[source_id],
                targets=[target_id],
            )
        )

    data.children[0].height += (
        makers.PORT_PADDING
        + (makers.PORT_SIZE + makers.PORT_PADDING) * len(components) // 2
    )


DERIVATORS: dict[type[common.GenericElement], DerivatorFunction] = {
    la.LogicalComponent: derive_from_functions,
    sa.SystemComponent: derive_from_functions,
}
"""Supported objects to build derived contexts for."""
