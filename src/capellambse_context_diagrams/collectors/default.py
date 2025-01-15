# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Default collector for the ContextDiagram.

Collection of
[`ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData] on
diagrams that involve ports.
"""

from __future__ import annotations

import collections.abc as cabc
import typing as t
from itertools import chain

import capellambse.model as m
from capellambse import helpers
from capellambse.metamodel import cs, fa, la, sa
from capellambse.model import DiagramType as DT

from .. import _elkjs
from . import exchanges, generic, makers

if t.TYPE_CHECKING:
    from .. import context

    DerivatorFunction: t.TypeAlias = cabc.Callable[
        [
            context.ContextDiagram,
            _elkjs.ELKInputData,
            dict[str, _elkjs.ELKInputChild],
        ],
        None,
    ]

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
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
        self.exchanges: dict[str, fa.AbstractExchange] = {}
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
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
            box.children = [self.centerbox]
            del self.data.children[0]

        self._process_ports()

        if self.diagram._display_parent_relation and self.diagram.target.owner:
            current = self.diagram.target.owner
            while (
                current
                and self.common_owners
                and hasattr(current, "owner")
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                current = generic.make_owner_box(
                    current,
                    self._make_box,
                    self.global_boxes,
                    self.boxes_to_delete,
                )
                self.common_owners.discard(current.uuid)

        for uuid in self.boxes_to_delete:
            del self.global_boxes[uuid]

        self.data.children.extend(self.global_boxes.values())
        if self.diagram._display_parent_relation:
            generic.move_parent_boxes_to_owner(
                self.made_boxes, self.diagram.target, self.data
            )
            generic.move_edges(
                self.made_boxes, self.exchanges.values(), self.data
            )

        if self.diagram._hide_direct_children:
            self.centerbox.children = []
            hidden = {edge.id for edge in self.centerbox.edges}
            centerbox_ports = {port.id for port in self.centerbox.ports}
            port_uuids: set[str] = set()
            for ex in self.exchanges.values():
                if ex.uuid not in hidden:
                    if ex.source.uuid in centerbox_ports:
                        port_uuids.add(ex.source.uuid)
                    if ex.target.uuid in centerbox_ports:
                        port_uuids.add(ex.target.uuid)

            self.centerbox.edges = []
            self.centerbox.ports = [
                p for p in self.centerbox.ports if p.id in port_uuids
            ]
            for label in self.centerbox.labels:
                label.layoutOptions = makers.CENTRIC_LABEL_LAYOUT_OPTIONS

    def _process_port_spread(
        self,
        exs: list[fa.AbstractExchange],
        attr: str,
        inc: int,
        port_spread: dict[str, int],
        owners: dict[str, str],
    ) -> None:
        for ex in exs:
            elem = getattr(ex, attr).owner
            if (owner := owners.get(elem.uuid)) is None:
                try:
                    owner = [
                        uuid
                        for uuid in generic.get_all_owners(elem)
                        if uuid not in self.diagram_target_owners
                    ][-1]
                except (IndexError, AttributeError):
                    owner = elem.uuid
                assert owner is not None
                owners[elem.uuid] = owner
            port_spread.setdefault(owner, 0)
            port_spread[owner] += inc

    def _process_exchanges(
        self,
    ) -> tuple[
        list[m.ModelElement],
        list[generic.ExchangeData],
    ]:
        inc, out = port_collector(self.diagram.target, self.diagram.type)
        inc_c = port_exchange_collector(inc.values())
        out_c = port_exchange_collector(out.values())
        inc_exchanges = list(chain.from_iterable(inc_c.values()))
        out_exchanges = list(chain.from_iterable(out_c.values()))
        port_spread: dict[str, int] = {}
        owners: dict[str, str] = {}
        self._process_port_spread(
            inc_exchanges, "source", 1, port_spread, owners
        )
        self._process_port_spread(
            out_exchanges, "target", -1, port_spread, owners
        )
        self.exchanges = {ex.uuid: ex for ex in inc_exchanges + out_exchanges}
        ex_datas: list[generic.ExchangeData] = []
        seen_exchanges: set[str] = set()
        for ex in self.exchanges.values():
            if ex.uuid in seen_exchanges:
                continue

            seen_exchanges.add(ex.uuid)
            if is_hierarchical := exchanges.is_hierarchical(
                ex, self.centerbox
            ):
                if not self.diagram._display_parent_relation:
                    continue
                self.centerbox.labels[
                    0
                ].layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
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
                src, tgt = generic.exchange_data_collector(ex_data)
                src_owner = owners.get(src.owner.uuid, "")
                tgt_owner = owners.get(tgt.owner.uuid, "")
                is_inc = tgt.parent == self.diagram.target
                is_out = src.parent == self.diagram.target
                if is_inc and is_out:
                    pass  # Support cycles
                elif (is_out and (port_spread.get(tgt_owner, 0) > 0)) or (
                    is_inc and (port_spread.get(src_owner, 0) <= 0)
                ):
                    elkdata.edges[-1].sources = [tgt.uuid]
                    elkdata.edges[-1].targets = [src.uuid]
                ex_datas.append(ex_data)
            except AttributeError:
                continue

        ports = list((inc | out).values())
        if not self.diagram._display_unused_ports:
            ports = [
                p for p in ports if (inc_c.get(p.uuid) or out_c.get(p.uuid))
            ]

        self.centerbox.height = max(
            self.centerbox.height,
            (makers.PORT_SIZE + 2 * makers.PORT_PADDING) * (len(ports) + 1),
        )
        for p in ports:
            port, height = self._make_port(p)
            self.centerbox.height += height

            self.centerbox.ports.append(port)
        self.centerbox.layoutOptions["portLabels.placement"] = "OUTSIDE"

        return ports, ex_datas

    def _process_ports(self) -> None:
        ports, ex_datas = self._process_exchanges()
        for owner, local_ports in port_context_collector(ex_datas, ports):
            _, label_height = helpers.get_text_extent(owner.name)
            height = max(
                label_height + 2 * makers.LABEL_VPAD,
                (makers.PORT_SIZE + 2 * makers.PORT_PADDING)
                * (len(local_ports) + 1),
            )
            local_port_objs = []
            for j in local_ports:
                port, label_heights = self._make_port(j)
                height += label_heights
                local_port_objs.append(port)

            if box := self.global_boxes.get(owner.uuid):
                if box is self.centerbox:
                    continue
                box.ports.extend(local_port_objs)
                box.height += height
            else:
                box = self._make_box(
                    owner,
                    height=height,
                )
                box.ports = local_port_objs

            box.layoutOptions["portLabels.placement"] = "OUTSIDE"

            if self.diagram._display_parent_relation:
                self.common_owners.add(
                    generic.make_owner_boxes(
                        owner,
                        self.diagram_target_owners,
                        self._make_box,
                        self.global_boxes,
                        self.boxes_to_delete,
                    )
                )

    def _make_port(
        self, port_obj: t.Any
    ) -> tuple[_elkjs.ELKInputPort, int | float]:
        port = makers.make_port(port_obj.uuid)
        height = 0.0
        if self.diagram._display_port_labels:
            port.labels = makers.make_label(port_obj.name)
            height += max(
                0,
                sum(label.height for label in port.labels)
                - 2 * makers.PORT_PADDING,
            )
        return port, height

    def _make_box(
        self,
        obj: t.Any,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        if box := self.global_boxes.get(obj.uuid):
            return box
        box = makers.make_box(
            obj,
            no_symbol=self.diagram._display_symbols_as_boxes,
            **kwargs,
        )
        self.global_boxes[obj.uuid] = box
        self.made_boxes[obj.uuid] = box
        return box


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
            processor.made_boxes,
        )
    return data


def port_collector(
    target: m.ModelElement | m.ElementList, diagram_type: DT
) -> tuple[dict[str, m.ModelElement], dict[str, m.ModelElement]]:
    """Collect ports from `target` savely."""

    def __collect(target):
        port_types = fa.FunctionPort | fa.ComponentPort | cs.PhysicalPort
        incoming_ports: dict[str, m.ModelElement] = {}
        outgoing_ports: dict[str, m.ModelElement] = {}
        for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram_type]:
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


class ContextInfo(t.NamedTuple):
    """ContextInfo data."""

    element: m.ModelElement
    """An element of context."""
    ports: list[m.ModelElement]
    """The context element's relevant ports.

    This list only contains ports that at least one of the exchanges
    passed into ``collect_exchanges`` sees.
    """


def port_context_collector(
    exchange_datas: t.Iterable[generic.ExchangeData],
    local_ports: t.Container[m.ModelElement],
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
    for exd in exchange_datas:
        try:
            source, target = generic.collect_exchange_endpoints(exd)
        except AttributeError:
            continue

        if source in local_ports:
            port = target
        elif target in local_ports:
            port = source
        else:
            continue

        try:
            owner = port.owner
        except AttributeError:
            continue

        info = ContextInfo(owner, [])
        info = ctx.setdefault(owner.uuid, info)
        if port not in info.ports:
            info.ports.append(port)

    return iter(ctx.values())


def derive_from_functions(
    diagram: context.ContextDiagram,
    data: _elkjs.ELKInputData,
    boxes: dict[str, _elkjs.ELKInputChild],
) -> None:
    """Derive Components from allocated functions of the context target.

    A Component, a ComponentExchange and two ComponentPorts are added
    to ``data``. These elements are prefixed with ``Derived-`` to
    receive special styling in the serialization step.
    """
    assert isinstance(diagram.target, cs.Component)
    ports: list[m.ModelElement] = []
    for fnc in diagram.target.allocated_functions:
        inc, out = port_collector(fnc, diagram.type)
        ports.extend((inc | out).values())

    derived_components: dict[str, cs.Component] = {}
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
                    or derived_comp.uuid in boxes
                ):
                    continue

                if derived_comp.uuid not in derived_components:
                    derived_components[derived_comp.uuid] = derived_comp
            except AttributeError:  # No owner of owner.
                pass

    # Idea: Include flow direction of derived interfaces from all functional
    # exchanges. Mixed means bidirectional. Just even out bidirectional
    # interfaces and keep flow direction of others.

    centerbox = boxes[diagram.target.uuid]
    i = 0
    for i, (uuid, derived_component) in enumerate(
        derived_components.items(), 1
    ):
        box = makers.make_box(
            derived_component,
            no_symbol=diagram._display_symbols_as_boxes,
        )
        class_ = diagram.serializer.get_styleclass(derived_component.uuid)
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

    centerbox.height += (
        makers.PORT_PADDING + (makers.PORT_SIZE + makers.PORT_PADDING) * i // 2
    )


DERIVATORS: dict[type[m.ModelElement], DerivatorFunction] = {
    la.LogicalComponent: derive_from_functions,
    sa.SystemComponent: derive_from_functions,
}
"""Supported objects to build derived contexts for."""
