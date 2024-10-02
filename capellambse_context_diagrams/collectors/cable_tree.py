# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines the collector for the CableTreeDiagram."""
from __future__ import annotations

import copy
import typing as t

import capellambse.model as m

from .. import _elkjs, context
from . import makers

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
        self.obj: m.ModelElement = self.diagram.target
        self.data = makers.make_diagram(diagram)
        self.data.layoutOptions = DEFAULT_LAYOUT_OPTIONS
        self.params = params
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}

    def __call__(self) -> _elkjs.ELKInputData:
        src_obj = self.obj.source
        tgt_obj = self.obj.target
        target_link = self._make_edge(self.obj, src_obj, tgt_obj)
        target_link.layoutOptions = copy.deepcopy(
            _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
        )
        self._make_tree(src_obj)
        self._make_tree(tgt_obj, reverse=True)
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
    """Main collector function for the CableTreeDiagram."""
    return CableTreeCollector(diagram, params)()
