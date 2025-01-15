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

import capellambse.model as m
from capellambse.metamodel import cs, fa, la, sa
from capellambse.model import DiagramType as DT

from .. import _elkjs
from . import custom, generic, makers

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


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect context data from ports of centric box."""
    visited: set[str] = set()
    edges: set[str] = set()

    def _default_collect(
        target: m.ModelElement,
    ) -> cabc.Iterator[m.ModelElement]:
        if target.uuid in visited:
            return
        visited.add(target.uuid)
        for port in (
            list(getattr(target, "inputs", []))
            + list(getattr(target, "outputs", []))
            + list(getattr(target, "ports", []))
            + list(getattr(target, "physical_ports", []))
        ):
            for exchange in list(getattr(port, "exchanges", [])) + list(
                getattr(port, "links", [])
            ):
                if exchange.uuid in edges:
                    continue
                edges.add(exchange.uuid)
                yield exchange
        for cmp in list(getattr(target, "components", [])):
            yield from _default_collect(cmp)

    diagram._collect = _default_collect(diagram.target)
    processor = custom.CustomCollector(diagram, params=params)
    processor()
    derivator = DERIVATORS.get(type(diagram.target))
    if diagram._display_derived_interfaces and derivator is not None:
        derivator(
            diagram,
            processor.data,
            processor.boxes,
        )
    return processor.data


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
