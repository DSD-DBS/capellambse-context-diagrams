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
    "layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    "spacing.labelNode": "0.0",
    "nodeSize.constraints": "NODE_LABELS",
    "aspectRatio": 1000,
    "layered.considerModelOrder.strategy": "PREFER_NODES",
    "layered.considerModelOrder.components": "MODEL_ORDER",
    "edgeRouting": "ORTHOGONAL",
}

DEFAULT_EDGE_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "spacing.edgeLabel": "0.0",
    "layered.edgeLabels.sideSelection": "SMART_DOWN",
}

DEFAULT_TREE_VIEW_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "algorithm": "layered",
    "elk.direction": "DOWN",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "edgeRouting": "POLYLINE",
    "nodeSize.constraints": "NODE_LABELS",
    "partitioning.active": True,
}


class ElementRelationProcessor:
    def __init__(
        self,
        diagram: context.ElementRelationViewDiagram,
        *,
        params: dict[str, t.Any] | None = None,
    ) -> None:
        self.diagram = diagram
        self.data = makers.make_diagram(diagram)
        self.data.layoutOptions = DEFAULT_LAYOUT_OPTIONS
        self.params = params or {}
        self.tree_view_box = _elkjs.ELKInputChild(
            id="__HideElement:tree-view",
            layoutOptions=DEFAULT_TREE_VIEW_LAYOUT_OPTIONS,
            children=[],
            edges=[],
        )
        self.left_box = _elkjs.ELKInputChild(
            id="__HideElement:left",
            layoutOptions=_elkjs.get_global_layered_layout_options(),
            children=[],
            edges=[],
        )
        self.right_box = _elkjs.ELKInputChild(
            id="__HideElement:right",
            layoutOptions=_elkjs.get_global_layered_layout_options(),
            children=[],
            edges=[],
        )
        self.left_boxes_n = 0
        self.global_boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.classes: dict[str, information.Class] = {}

    def process(self) -> None:
        for item in self.diagram.target.allocated_exchange_items:
            if not (parent_box := self.global_boxes.get(item.parent.uuid)):
                parent_box = self.global_boxes.setdefault(
                    item.parent.uuid,
                    makers.make_box(
                        item.parent,
                        layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
                    ),
                )
                self.left_box.children.append(parent_box)

            if item.uuid in (i.id for i in parent_box.children):
                continue
            box = makers.make_box(item)
            parent_box.children.append(box)
            self.left_boxes_n += 1

            for elem in item.elements:
                if elem.abstract_type:
                    self.classes.setdefault(
                        elem.abstract_type.uuid, elem.abstract_type
                    )
                    eid = f"__ExchangeItemElement:{item.uuid}_{elem.abstract_type.uuid}"
                    self.data.edges.append(
                        _elkjs.ELKInputEdge(
                            id=eid,
                            layoutOptions=DEFAULT_EDGE_LAYOUT_OPTIONS,
                            sources=[item.uuid],
                            targets=[elem.abstract_type.uuid],
                            labels=makers.make_label(elem.name),
                        )
                    )
        for cls in self.classes.values():
            box = self._make_class_box(cls)
            partition = 0
            current = cls
            while current.super and current.super.uuid in self.classes:
                partition += 1
                current = current.super
            box.layoutOptions["partitioning.partition"] = partition
            self.tree_view_box.children.append(box)
            if partition > 0:
                eid = f"__Generalization:{cls.super.uuid}_{cls.uuid}"
                self.tree_view_box.edges.append(
                    _elkjs.ELKInputEdge(
                        id=eid,
                        sources=[cls.super.uuid],
                        targets=[cls.uuid],
                    )
                )

        right_boxes_n = 0
        while self.left_boxes_n > right_boxes_n:
            box = self.left_box.children.pop()
            self.right_box.children.append(box)
            n = len(box.children)
            self.left_boxes_n -= n
            right_boxes_n += n

        if not self.global_boxes:
            logger.warning("Nothing to see here")
            return
        self.data.children.extend(
            [self.left_box, self.tree_view_box, self.right_box]
        )

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
    diagram: context.ElementRelationViewDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    processor = ElementRelationProcessor(diagram, params=params)
    processor.process()
    return processor.data
