# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines the collector for the CustomDiagram."""
from __future__ import annotations

import collections.abc as cabc
import copy
import typing as t

import capellambse.model as m

from .. import _elkjs, context
from . import generic, makers


def _is_edge(obj: m.ModelElement) -> bool:
    if hasattr(obj, "source") and hasattr(obj, "target"):
        return True
    return False


def _is_port(obj: m.ModelElement) -> bool:
    if obj.xtype.endswith("Port"):
        return True
    return False


class CustomCollector:
    """Collect the context for a custom diagram."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.target: m.ModelElement = self.diagram.target

        self.boxable_target: m.ModelElement
        if _is_port(self.target):
            self.boxable_target = self.target.owner
        elif _is_edge(self.target):
            self.boxable_target = self.target.source.owner
        else:
            self.boxable_target = self.target

        self.data = makers.make_diagram(diagram)
        self.params = params
        self.instructions = self.diagram._collect
        self.repeat_instructions: dict[str, t.Any] = {}
        self.repeat_depth: int = 0
        self.visited: set[str] = set()
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.boxes_to_delete: set[str] = set()

        if self.diagram._display_parent_relation:
            self.edge_owners: dict[str, str] = {}
            self.diagram_target_owners = list(
                generic.get_all_owners(self.boxable_target)
            )
            self.common_owners: set[str] = set()

        if self.diagram._unify_edge_direction != "NONE":
            self.directions: dict[str, bool] = {}
        self.min_heights: dict[str, dict[str, float]] = {}

    def __call__(self) -> _elkjs.ELKInputData:
        if _is_port(self.target):
            self._make_port_and_owner(self.target)
        else:
            self._make_target(self.target)
        if target_edge := self.edges.get(self.target.uuid):
            target_edge.layoutOptions = copy.deepcopy(
                _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
            )
        if not self.instructions:
            return self._get_data()
        if self.diagram._unify_edge_direction == "UNIFORM":
            self.directions[self.boxable_target.uuid] = False
        self._perform_instructions(self.target, self.instructions)
        if self.diagram._display_parent_relation:
            current = self.boxable_target
            while (
                current
                and self.common_owners
                and getattr(current, "owner", None) is not None
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                current = self._make_owner_box(
                    current,
                )
                self.common_owners.discard(current.uuid)
            for edge_uuid, box_uuid in self.edge_owners.items():
                if box := self.boxes.get(box_uuid):
                    box.edges.append(self.edges.pop(edge_uuid))

        self._fix_box_heights()
        for uuid in self.boxes_to_delete:
            del self.boxes[uuid]
        return self._get_data()

    def _get_data(self) -> t.Any:
        self.data.children = list(self.boxes.values())
        self.data.edges = list(self.edges.values())
        return self.data

    def _fix_box_heights(self) -> None:
        if self.diagram._unify_edge_direction != "NONE":
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max(box.height, sum(min_heights.values()))
        else:
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max([box.height] + list(min_heights.values()))

    def _matches_filters(
        self, obj: m.ModelElement, filters: dict[str, t.Any]
    ) -> bool:
        for key, value in filters.items():
            if getattr(obj, key) != value:
                return False
        return True

    def _perform_instructions(
        self, obj: m.ModelElement, instructions: dict[str, t.Any]
    ) -> None:
        if max_depth := instructions.pop("repeat", None):
            self.repeat_instructions = instructions
            self.repeat_depth = max_depth
        if get_targets := instructions.get("get"):
            self._perform_get_or_include(obj, get_targets, False)
        if include_targets := instructions.get("include"):
            self._perform_get_or_include(obj, include_targets, True)
        if not get_targets and not include_targets:
            if self.repeat_depth != 0:
                self.repeat_depth -= 1
                self._perform_instructions(obj, self.repeat_instructions)

    def _perform_get_or_include(
        self,
        obj: m.ModelElement,
        targets: dict[str, t.Any] | list[dict[str, t.Any]],
        create: bool,
    ) -> None:
        if isinstance(targets, dict):
            targets = [targets]
        assert isinstance(targets, list)
        if self.repeat_depth > 0:
            self.repeat_depth += len(targets)
        for i in targets:
            attr = i.get("name")
            assert attr, "Attribute name is required."
            target = getattr(obj, attr, None)
            if isinstance(target, cabc.Iterable):
                filters = i.get("filter", {})
                for item in target:
                    if item.uuid in self.visited:
                        continue
                    self.visited.add(item.uuid)
                    if not self._matches_filters(item, filters):
                        continue
                    if create:
                        self._make_target(item)
                    self._perform_instructions(item, i)
            elif isinstance(target, m.ModelElement):
                if target.uuid in self.visited:
                    continue
                self.visited.add(target.uuid)
                if create:
                    self._make_target(target)
                self._perform_instructions(target, i)

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
        src_owners = list(generic.get_all_owners(src_obj))
        tgt_owners = list(generic.get_all_owners(tgt_obj))
        if self.diagram._hide_direct_children:
            if (
                self.boxable_target.uuid in src_owners
                or self.boxable_target.uuid in tgt_owners
            ):
                return None
        if self.diagram._display_parent_relation:
            common_owner = None
            for owner in src_owners:
                if owner in tgt_owners:
                    common_owner = owner
                    break
            if common_owner:
                self.edge_owners[edge_obj.uuid] = common_owner

        if self._need_switch(
            src_owners, tgt_owners, src_owner.uuid, tgt_owner.uuid
        ):
            src_obj, tgt_obj = tgt_obj, src_obj
            src_owner, tgt_owner = tgt_owner, src_owner

        if not self.ports.get(src_obj.uuid):
            port = self._make_port_and_owner(src_obj)
            self.min_heights.setdefault(
                src_owner.uuid, {"left": 0.0, "right": 0.0}
            )["right"] += makers.PORT_SIZE + max(
                2 * makers.PORT_PADDING,
                sum(label.height for label in port.labels),
            )
        if not self.ports.get(tgt_obj.uuid):
            port = self._make_port_and_owner(tgt_obj)
            self.min_heights.setdefault(
                tgt_owner.uuid, {"left": 0.0, "right": 0.0}
            )["left"] += makers.PORT_SIZE + max(
                2 * makers.PORT_PADDING,
                sum(label.height for label in port.labels),
            )

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

    def _need_switch(
        self,
        src_owners: list[str],
        tgt_owners: list[str],
        src_uuid: str,
        tgt_uuid: str,
    ) -> bool:
        if self.diagram._unify_edge_direction == "SMART":
            if src_uuid != self.boxable_target.uuid:
                src_uncommon = [
                    owner for owner in src_owners if owner not in tgt_owners
                ][-1]
                src_dir = self.directions.setdefault(src_uncommon, False)
            else:
                src_dir = None
            if tgt_uuid != self.boxable_target.uuid:
                tgt_uncommon = [
                    owner for owner in tgt_owners if owner not in src_owners
                ][-1]
                tgt_dir = self.directions.setdefault(tgt_uncommon, True)
            else:
                tgt_dir = None
            if (src_dir is True) or (tgt_dir is False):
                return True
        elif self.diagram._unify_edge_direction == "UNIFORM":
            src_dir = self.directions.get(src_uuid)
            tgt_dir = self.directions.get(tgt_uuid)
            if (src_dir is None) and (tgt_dir is None):
                self.directions[src_uuid] = False
                self.directions[tgt_uuid] = True
            elif src_dir is None:
                self.directions[src_uuid] = not tgt_dir
            elif tgt_dir is None:
                self.directions[tgt_uuid] = not src_dir
            if self.directions[src_uuid]:
                return True
        elif self.diagram._unify_edge_direction == "TREE":
            src_dir = self.directions.get(src_uuid)
            tgt_dir = self.directions.get(tgt_uuid)
            if (src_dir is None) and (tgt_dir is None):
                self.directions[src_uuid] = True
                self.directions[tgt_uuid] = True
            elif src_dir is None:
                self.directions[src_uuid] = True
                return True
            elif tgt_dir is None:
                self.directions[tgt_uuid] = True
        return False

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
            _plp = self.diagram._port_label_position
            if not (plp := getattr(_elkjs.PORT_LABEL_POSITION, _plp, None)):
                raise ValueError(f"Invalid port label position '{_plp}'.")
            assert isinstance(plp, _elkjs.PORT_LABEL_POSITION)
            box.layoutOptions["portLabels.placement"] = plp.name
        box.ports.append(port)
        self.ports[port_obj.uuid] = port
        return port


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect data for rendering a custom diagram."""
    return CustomCollector(diagram, params)()
