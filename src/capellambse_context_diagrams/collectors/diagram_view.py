# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the DiagramView.

Functionality for collecting all model elements from a [`Diagram`][capellambse.model.diagram.Diagram]
and conversion of it into [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
for an automated layout.
"""

from __future__ import annotations

import logging
import typing as t

from capellambse import model as m
from capellambse.metamodel import cs, fa

from .. import _elkjs, context
from . import generic, makers

logger = logging.getLogger(__name__)
PortTypes: t.TypeAlias = fa.FunctionPort | fa.ComponentPort | cs.PhysicalPort


def is_function(node: m.ModelElement) -> bool:
    """Check if the ``node`` is a function."""
    return isinstance(node, fa.Function)


def is_part(node: m.ModelElement) -> bool:
    """Check if the ``node`` is a part."""
    return node.xtype.endswith("Part")


def is_exchange(node: m.ModelElement) -> bool:
    """Check if the ``node`` is an exchange."""
    return hasattr(node, "source") and hasattr(node, "target")


def is_allocation(node: m.ModelElement) -> bool:
    """Check if the ``node`` is an allocation."""
    return node.xtype.endswith("PortAllocation")


def is_port(node: m.ModelElement) -> bool:
    """Check if the ``node`` is a port."""
    return node.xtype.endswith("Port")


class Collector:
    """Collects all model elements from a diagram for ELK."""

    def __init__(self, diagram: context.ELKDiagram):
        self.diagram = diagram
        self._diagram = diagram.target
        self.data = generic.collector(self.diagram, no_symbol=True)
        self.data.children = []

        self.made_elements: dict[
            str,
            _elkjs.ELKInputChild | _elkjs.ELKInputEdge | _elkjs.ELKInputPort,
        ] = {}
        self.made_boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.made_ports: dict[str, _elkjs.ELKInputPort] = {}
        self.exchanges: dict[str, fa.AbstractExchange] = {}
        self.global_boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.ports: dict[str, PortTypes] = {}
        self.boxes_to_delete: set[str] = set()

    def __call__(self, params: dict[str, t.Any]) -> _elkjs.ELKInputData:
        self._get_data(params)
        self._adjust_box_sizes(params)
        self._solve_hierarchy(params)
        return self.data

    def _get_data(self, params: dict[str, t.Any]):
        del params  # No use for it now
        for node in self._diagram.nodes:
            if is_function(node):
                self.make_all_owner_boxes(node)
            elif is_part(node):
                self.make_all_owner_boxes(node.type)
            elif is_exchange(node) and not is_allocation(node):
                self.exchanges[node.uuid] = node  # type: ignore[assignment]
                edge = _elkjs.ELKInputEdge(
                    id=node.uuid,
                    sources=[node.source.uuid],
                    targets=[node.target.uuid],
                    labels=makers.make_label(
                        node.name, max_width=makers.MAX_LABEL_WIDTH
                    ),
                )
                self.ports[node.source.uuid] = node.source
                self.ports[node.target.uuid] = node.target
                self.data.edges.append(edge)
            elif is_port(node):
                self.made_ports[node.uuid] = (port := self._make_port(node))
                self.made_boxes[node.owner.uuid].ports.append(port)

        if leftover_ports := set(self.ports) - set(self.made_ports):
            logger.debug(
                "There are ports missing in the diagram nodes: %r",
                leftover_ports,
            )
            for uuid in leftover_ports:
                port_obj = self.ports[uuid]
                self.made_ports[uuid] = (port := self._make_port(port_obj))
                self.made_boxes[port_obj.owner.uuid].ports.append(port)

        for uuid in self.boxes_to_delete:
            del self.global_boxes[uuid]

        self.data.children.extend(self.global_boxes.values())

    def make_all_owner_boxes(self, obj: m.ModelElement):
        """Make boxes for all owners of the given object.

        Notes
        -----
        Also makes a box for the object itself.
        """
        if not (obj_box := self.made_boxes.get(obj.uuid)):
            obj_box = self._make_box(obj, no_symbol=True, slim_width=False)
            self.made_boxes[obj.uuid] = obj_box

        current: m.ModelElement | None = obj
        while (
            current
            and hasattr(current, "owner")
            and not isinstance(current.owner, generic.PackageTypes)
        ):
            current = self._make_owner_box(current)

    def _make_owner_box(self, obj: m.ModelElement) -> m.ModelElement | None:
        if obj.owner.uuid in self.diagram._hide_elements:
            return None

        if not (parent_box := self.made_boxes.get(obj.owner.uuid)):
            parent_box = self._make_box(
                obj.owner,
                no_symbol=True,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
        assert (obj_box := self.made_boxes.get(obj.uuid))
        for box in (children := parent_box.children):
            if box.id == obj.uuid:
                box = obj_box
                break
        else:
            children.append(obj_box)
            for label in parent_box.labels:
                label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS

        self.boxes_to_delete.add(obj.uuid)
        return obj.owner

    def _make_box(
        self, obj: m.ModelElement, **kwargs: t.Any
    ) -> _elkjs.ELKInputChild:
        box = makers.make_box(obj, **kwargs)
        self.global_boxes[obj.uuid] = box
        self.made_boxes[obj.uuid] = box
        return box

    def _make_port(self, obj: m.ModelElement) -> _elkjs.ELKInputPort:
        if self.diagram._display_port_labels:
            label = obj.name or "UNKNOWN"
        else:
            label = ""

        return makers.make_port(obj.uuid, label=label)

    def _adjust_box_sizes(self, params: dict[str, t.Any]):
        del params  # No use for it now
        for box in self.made_boxes.values():
            box.height += (makers.PORT_SIZE + 2 * makers.PORT_PADDING) * (
                len(box.ports) + 1
            )

    def _solve_hierarchy(self, params: dict[str, t.Any]):
        del params  # No use for it now
        generic.move_edges(self.made_boxes, self.exchanges.values(), self.data)


def collect_from_diagram(
    diagram: context.ELKDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Return ``ELKInputData`` from a diagram."""
    diagram._slim_center_box = False
    return Collector(diagram)(params)
