# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import math
import typing as t

from capellambse.model.crosslayer import information

from .. import _elkjs, context
from . import makers, tree_view

logger = logging.getLogger(__name__)

DEFAULT_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "algorithm": "layered",
    "elk.direction": "RIGHT",
    "layered.nodePlacement.strategy": "LINEAR_SEGMENTS",
    "edgeStraightening": "NONE",
    "spacing.labelNode": "0.0",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "edgeRouting": "POLYLINE",
    "nodeSize.constraints": "NODE_LABELS",
    "hierarchyHandling": "INCLUDE_CHILDREN",
    "layered.spacing.edgeEdgeBetweenLayers": "2.0",
}


class ExchangeItemRelationCollector:
    def __init__(
        self,
        diagram: context.ExchangeItemRelationViewDiagram,
        *,
        params: dict[str, t.Any] | None = None,
    ) -> None:
        self.diagram = diagram
        self.data = makers.make_diagram(diagram)
        self.data.layoutOptions = DEFAULT_LAYOUT_OPTIONS
        self.params = params or {}
        self.global_boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.classes: dict[str, information.Class] = {}
        self.edges: dict[str, list[_elkjs.ELKInputEdge]] = {}

    def __call__(self) -> _elkjs.ELKInputData:
        if not self.diagram.target.exchange_items:
            logger.warning("No exchange items to display")
            return self.data
        for item in self.diagram.target.exchange_items:
            if not (parent_box := self.global_boxes.get(item.parent.uuid)):
                parent_box = self.global_boxes.setdefault(
                    item.parent.uuid,
                    makers.make_box(
                        item.parent,
                        layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
                    ),
                )

            if item.uuid in (i.id for i in parent_box.children):
                continue
            box = makers.make_box(item)
            parent_box.children.append(box)

            for elem in item.elements:
                if elem.abstract_type is None:
                    continue
                self.classes.setdefault(
                    elem.abstract_type.uuid, elem.abstract_type
                )
                eid = f"__ExchangeItemElement:{item.uuid}_{elem.abstract_type.uuid}"
                edge = _elkjs.ELKInputEdge(
                    id=eid,
                    sources=[item.uuid],
                    targets=[elem.abstract_type.uuid],
                    labels=makers.make_label(
                        elem.name,
                    ),
                )
                self.data.edges.append(edge)
                self.edges.setdefault(item.parent.uuid, []).append(edge)

        for cls in self.classes.values():
            box = self._make_class_box(cls)
            self.data.children.append(box)
            if cls.super:
                eid = f"__Generalization:{cls.super.uuid}_{cls.uuid}"
                self.data.edges.append(
                    _elkjs.ELKInputEdge(
                        id=eid,
                        sources=[cls.super.uuid],
                        targets=[cls.uuid],
                    )
                )

        top = sum(len(box.children) for box in self.global_boxes.values())
        mid = top / 2
        ordered = list(self.global_boxes.keys())
        for uuid in ordered:
            if top < mid:
                break
            self.data.edges.append(
                _elkjs.ELKInputEdge(
                    id=f"__Hide{uuid}",
                    sources=[uuid],
                    targets=[ordered[-1]],
                )
            )
            for edge in self.edges.get(uuid, []):
                edge.sources, edge.targets = edge.targets, edge.sources
                edge.id = f"__Reverse-{edge.id[2:]}"
            top -= len(self.global_boxes[uuid].children)

        self.data.children.extend(self.global_boxes.values())
        return self.data

    def _make_class_box(self, cls: information.Class) -> _elkjs.ELKInputChild:
        box = makers.make_box(
            cls, layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS
        )
        properties = [
            _elkjs.ELKInputLabel(
                text="",
                layoutOptions=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
                width=0,
                height=0,
            )
        ]
        for prop in cls.properties:
            if prop.type is None or (
                isinstance(prop.type, information.Class)
                and not prop.type.is_primitive
            ):
                continue

            text = tree_view._get_property_text(prop)
            labels = makers.make_label(
                text,
                icon=(makers.ICON_WIDTH, 0),
                layout_options=tree_view.DATA_TYPE_LABEL_LAYOUT_OPTIONS,
                max_width=math.inf,
            )
            properties.extend(labels)

        box.labels.extend(properties)
        box.width, box.height = makers.calculate_height_and_width(properties)
        return box


def collector(
    diagram: context.ExchangeItemRelationViewDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Return ExchangeElement data for ELK."""
    return ExchangeItemRelationCollector(diagram, params=params)()
