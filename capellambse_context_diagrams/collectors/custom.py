# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines the collector for the CustomDiagram."""
from __future__ import annotations

import collections.abc as cabc
import typing as t

import capellambse.model as m

from .. import _elkjs, context
from . import generic, makers


class CustomCollector:
    """Collect the context for a custom diagram."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.obj: m.ModelElement = self.diagram.target
        self.data = makers.make_diagram(diagram)
        self.params = params
        self.instructions = self.diagram._collect
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.boxes_to_delete: set[str] = set()
        if self.diagram._display_parent_relation:
            self.diagram_target_owners = list(
                generic.get_all_owners(self.diagram.target)
            )
            self.common_owners: set[str] = set()
        if self.diagram._unify_edge_direction:
            self.dicrections: dict[str, bool] = {}

    def __call__(self) -> _elkjs.ELKInputData:
        self._make_target(self.obj)
        if not self.instructions:
            return self._get_data()
        self._perform_get(self.obj, self.instructions)
        if self.diagram._display_parent_relation and self.obj.owner:
            current = self.obj.owner
            while (
                current
                and self.common_owners
                and hasattr(current, "owner")
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                current = self._make_owner_box(
                    current,
                )
                self.common_owners.discard(current.uuid)
        for uuid in self.boxes_to_delete:
            del self.boxes[uuid]
        return self._get_data()

    def _get_data(self) -> t.Any:
        self.data.children = list(self.boxes.values())
        self.data.edges = list(self.edges.values())
        return self.data

    def _matches_filters(
        self, obj: m.ModelElement, filters: dict[str, t.Any]
    ) -> bool:
        for key, value in filters.items():
            if getattr(obj, key) != value:
                return False
        return True

    def _perform_get(
        self, obj: m.ModelElement, instructions: dict[str, t.Any]
    ) -> None:
        if insts := instructions.get("get"):
            create = False
        elif insts := instructions.get("include"):
            create = True
        if not insts:
            return
        if isinstance(insts, dict):
            insts = [insts]
        assert isinstance(insts, list)
        for i in insts:
            attr = i.get("name")
            assert attr, "Attribute name is required."
            target = getattr(obj, attr, None)
            if isinstance(target, cabc.Iterable):
                filters = i.get("filter", {})
                for item in target:
                    if not self._matches_filters(item, filters):
                        continue
                    if create:
                        self._make_target(item)
                    self._perform_get(item, i)
            elif isinstance(target, m.ModelElement):
                if create:
                    self._make_target(target)
                self._perform_get(target, i)

    def _make_target(
        self, obj: m.ModelElement
    ) -> _elkjs.ELKInputChild | _elkjs.ELKInputEdge | None:
        if _is_edge(obj):
            return self._make_edge_and_ports(obj)
        return self._make_box(obj, slim_width=self.diagram._slim_center_box)

    def _make_box(
        self,
        obj: m.ModelElement,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        box = makers.make_box(
            obj,
            no_symbol=self.diagram._display_symbols_as_boxes,
            **kwargs,
        )
        self.boxes[obj.uuid] = box
        if self.diagram._display_unused_ports:
            for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[
                self.diagram.type
            ]:
                for port in getattr(obj, attr, []):
                    self._make_port_and_owner(port)
        if self.diagram._display_parent_relation:
            current = obj
            while (
                current
                and current.uuid not in self.diagram_target_owners
                and getattr(current, "owner", None) is not None
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                current = self._make_owner_box(current)
            self.common_owners.add(current.uuid)
        return box

    def _make_owner_box(
        self,
        obj: t.Any,
    ) -> t.Any:
        if not (parent_box := self.boxes.get(obj.owner.uuid)):
            parent_box = self._make_box(
                obj.owner,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
        assert (obj_box := self.boxes.get(obj.uuid))
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

    def _make_edge_and_ports(
        self,
        edge_obj: m.ModelElement,
    ) -> _elkjs.ELKInputEdge | None:
        src_obj = edge_obj.source
        tgt_obj = edge_obj.target
        src_owner = src_obj.owner
        tgt_owner = tgt_obj.owner
        if self.diagram._hide_direct_children:
            if (
                getattr(src_owner, "owner", None) == self.obj
                or getattr(tgt_owner, "owner", None) == self.obj
            ):
                return None
        if self.diagram._unify_edge_direction:
            src_dir = self.dicrections.get(src_owner.uuid)
            tgt_dir = self.dicrections.get(tgt_owner.uuid)
            if (src_dir is None) and (tgt_dir is None):
                self.dicrections[src_owner.uuid] = False
                self.dicrections[tgt_owner.uuid] = True
            elif src_dir is None:
                self.dicrections[src_owner.uuid] = not tgt_dir
            elif tgt_dir is None:
                self.dicrections[tgt_owner.uuid] = not src_dir
            if self.dicrections[src_owner.uuid]:
                src_obj, tgt_obj = tgt_obj, src_obj
        self._make_port_and_owner(src_obj)
        self._make_port_and_owner(tgt_obj)
        edge = _elkjs.ELKInputEdge(
            id=edge_obj.uuid,
            sources=[src_obj.uuid],
            targets=[tgt_obj.uuid],
            labels=makers.make_label(
                edge_obj.name,
            ),
        )
        self.edges[edge_obj.uuid] = edge
        return edge

    def _make_port_and_owner(
        self, port_obj: m.ModelElement
    ) -> _elkjs.ELKInputPort:
        owner_obj = port_obj.owner
        if not (box := self.boxes.get(owner_obj.uuid)):
            box = self._make_box(
                owner_obj,
                layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            )
        if port := self.ports.get(port_obj.uuid):
            return port
        port = makers.make_port(port_obj.uuid)
        if self.diagram._display_port_labels:
            text = port_obj.name or "UNKNOWN"
            port.labels = makers.make_label(text)
        box.ports.append(port)
        self.ports[port_obj.uuid] = port
        return port


def _is_edge(obj: m.ModelElement) -> bool:
    styleclass = obj.xtype.rsplit(":", 1)[-1]
    for sub_str in ("Link", "Exchange"):
        if sub_str in styleclass:
            return True
    return False


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect data for rendering a custom diagram."""
    return CustomCollector(diagram, params)()
