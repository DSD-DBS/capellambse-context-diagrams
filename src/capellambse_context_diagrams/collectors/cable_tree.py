# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the CableTreeDiagram."""

from __future__ import annotations

import typing as t

import capellambse.model as m

from .. import _elkjs, context
from . import generic, makers

DEFAULT_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
}


class CableTreeCollector:
    """Collect the context for ``PhysicalLink`` trees."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.src_port_obj: m.ModelElement = self.diagram.target.source
        self.tgt_port_obj: m.ModelElement = self.diagram.target.target
        self.src_obj: m.ModelElement = self.src_port_obj.owner
        self.tgt_obj: m.ModelElement = self.tgt_port_obj.owner
        self.data = makers.make_diagram(diagram)
        self.data.layoutOptions = DEFAULT_LAYOUT_OPTIONS
        self.params = params
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.common_owner: str | None = None

    def __call__(self) -> _elkjs.ELKInputData:
        if self.src_obj.uuid in set(generic.get_all_owners(self.tgt_obj)):
            self.common_owner = self.src_obj.uuid
        elif self.tgt_obj.uuid in set(generic.get_all_owners(self.src_obj)):
            self.common_owner = self.tgt_obj.uuid
        self._make_tree(self.src_port_obj)
        self._make_tree(self.tgt_port_obj, reverse=True)
        return self.data

    def _make_tree(
        self, port_obj: m.ModelElement, reverse: bool = False
    ) -> _elkjs.ELKInputChild:
        box = self._make_port_and_owner(port_obj)
        for link in port_obj.links:
            if self.edges.get(link.uuid):
                continue
            if link.source.uuid == port_obj.uuid:
                obj = link.target
            else:
                obj = link.source
            owners = list(generic.get_all_owners(obj))[2:]
            if self.common_owner:
                if self.common_owner not in owners:
                    continue
            elif (self.src_obj.uuid in owners) or (
                self.tgt_obj.uuid in owners
            ):
                continue
            if reverse:
                self._make_edge(link, obj, port_obj)
            else:
                self._make_edge(link, port_obj, obj)
            self._make_tree(obj, reverse=reverse)
        return box

    def _make_edge(
        self,
        link: m.ModelElement,
        src_obj: m.ModelElement,
        tgt_obj: m.ModelElement,
    ) -> _elkjs.ELKInputEdge:
        edge = _elkjs.ELKInputEdge(
            id=link.uuid,
            sources=[src_obj.uuid],
            targets=[tgt_obj.uuid],
            labels=makers.make_label(
                link.name,
            ),
        )
        self.data.edges.append(edge)
        self.edges[link.uuid] = edge
        return edge

    def _make_port_and_owner(
        self, port_obj: m.ModelElement
    ) -> _elkjs.ELKInputChild:
        owner_obj = port_obj.owner
        if not (box := self.boxes.get(owner_obj.uuid)):
            box = makers.make_box(
                owner_obj,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
            self.boxes[owner_obj.uuid] = box
            self.data.children.append(box)
        if port := self.ports.get(port_obj.uuid):
            return box
        port = makers.make_port(port_obj.uuid)
        if self.diagram._display_port_labels:
            text = port_obj.name or "UNKNOWN"
            port.labels = makers.make_label(text)
        box.ports.append(port)
        self.ports[port_obj.uuid] = port
        return box


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect model elements for the CableTreeDiagram."""
    return CableTreeCollector(diagram, params)()
