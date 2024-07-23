# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import math
import typing as t

from capellambse.model import common
from capellambse.model.crosslayer import cs, fa, information
from capellambse.model.modeltypes import DiagramType as DT

from .. import _elkjs, context
from . import generic, makers, tree_view

logger = logging.getLogger(__name__)

DEFAULT_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "algorithm": "sporeOverlap",
    "elk.underlyingLayoutAlgorithm": "radial",
    "elk.spacing.nodeNode": 20,
    "elk.spacing.edgeNode": 10,
    "elk.edgeLabels.inline": True,
    "elk.radial.compactor": "WEDGE_COMPACTION",
}


class ElementRelationProcessor:
    def __init__(
        self,
        diagram: context.ElementRelationViewDiagram,
        data: _elkjs.ELKInputData,
        *,
        params: dict[str, t.Any] | None = None,
    ) -> None:
        self.diagram = diagram
        self.data = data
        self.params = params or {}
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
            if item.uuid in (i.id for i in parent_box.children):
                continue
            box = makers.make_box(item)
            parent_box.children.append(box)

            for elem in item.elements:
                if elem.abstract_type:
                    self.classes.setdefault(
                        elem.abstract_type.uuid, elem.abstract_type
                    )
                    self.data.edges.append(
                        _elkjs.ELKInputEdge(
                            id=f"__ExchangeItemElement:{elem.uuid}",
                            sources=[item.uuid],
                            targets=[elem.abstract_type.uuid],
                            labels=makers.make_label(elem.name),
                        )
                    )
        for cls in self.classes.values():
            self.global_boxes.setdefault(cls.uuid, self._make_class_box(cls))
            if cls.super and cls.super.uuid in self.classes:
                self.data.edges.append(
                    _elkjs.ELKInputEdge(
                        id=f"__Generalization:{cls.uuid}",
                        sources=[cls.uuid],
                        targets=[cls.super.uuid],
                    )
                )
        if not self.global_boxes:
            logger.warning("Nothing to see here")
            return
        self.data.children.extend(self.global_boxes.values())

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
            if (
                prop.type is None
                or (
                    isinstance(prop.type, information.Class)
                    or isinstance(prop.type, information.datatype.Enumeration)
                )
                and prop.type.is_primitive
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
    data = makers.make_diagram(diagram)
    # data.layoutOptions = DEFAULT_LAYOUT_OPTIONS
    processor = ElementRelationProcessor(diagram, data, params=params)
    processor.process()
    return data
