# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""This submodule defines the collector for the Class-Tree diagram."""
from __future__ import annotations

import collections.abc as cabc
import copy
import dataclasses
import logging
import math
import typing as t

from capellambse.model.crosslayer import information

from .. import _elkjs, context
from . import generic, makers

logger = logging.getLogger(__name__)
DATA_TYPE_LABEL_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "nodeLabels.placement": "INSIDE, V_CENTER, H_CENTER"
}
DEFAULT_LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "algorithm": "layered",
    "elk.direction": "DOWN",
    "edgeRouting": "ORTHOGONAL",
}


class ClassProcessor:
    def __init__(
        self,
        data: _elkjs.ELKInputData,
        all_associations: cabc.Iterable[information.Association],
    ) -> None:
        self.data = data
        self.made_boxes: set[str] = {data["children"][0]["id"]}
        self.made_edges: set[str] = set()
        self.data_types: set[str] = set()
        self.legend_boxes: list[_elkjs.ELKInputChild] = []
        self.all_associations = all_associations

    def __contains__(self, uuid: str) -> bool:
        objects = self.data["children"] + self.data["edges"]  # type: ignore[operator]
        return uuid in {obj["id"] for obj in objects}

    def process_class(self, cls, params):
        self._process_box(cls.source, cls.partition, params)

        if not cls.primitive and isinstance(cls.target, information.Class):
            self._process_box(cls.target, cls.partition, params)
            edges = [
                assoc
                for assoc in self.all_associations
                if cls.prop in assoc.navigable_members
            ]
            assert len(edges) == 1
            if (edge_id := edges[0].uuid) not in self.made_edges:
                self.made_edges.add(edge_id)
                text = cls.prop.name
                start, end = cls.multiplicity
                if start != "1" or end != "1":
                    text = f"[{start}..{end}] {text}"
                self.data["edges"].append(
                    {
                        "id": edge_id,
                        "sources": [cls.source.uuid],
                        "targets": [cls.target.uuid],
                        "labels": [makers.make_label(text)],
                    }
                )

        if cls.generalizes:
            self._process_box(cls.generalizes, cls.partition, params)
            edge = cls.generalizes.generalizations.by_super(
                cls.source, single=True
            )
            if edge.uuid not in self.made_edges:
                self.made_edges.add(edge.uuid)
                self.data["edges"].append(
                    {
                        "id": edge.uuid,
                        "sources": [cls.generalizes.uuid],
                        "targets": [cls.source.uuid],
                    }
                )

    def _process_box(
        self, obj: information.Class, partition: int, params: dict[str, t.Any]
    ) -> None:
        if obj.uuid not in self.made_boxes:
            self._make_box(obj, partition, params)

    def _make_box(
        self, obj: information.Class, partition: int, params: dict[str, t.Any]
    ) -> _elkjs.ELKInputChild:
        self.made_boxes.add(obj.uuid)
        box = makers.make_box(obj)
        self._set_data_types_and_labels(box, obj)
        _set_partitioning(box, partition, params)
        self.data["children"].append(box)
        return box

    def _set_data_types_and_labels(
        self, box: _elkjs.ELKInputChild, target: information.Class
    ) -> None:
        properties, legends = _get_all_non_edge_properties(
            target, self.data_types
        )
        box["labels"].extend(properties)
        box["width"], box["height"] = makers.calculate_height_and_width(
            list(box["labels"])
        )
        for legend in legends:
            if legend["id"] not in self:
                self.legend_boxes.append(legend)


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> tuple[_elkjs.ELKInputData, _elkjs.ELKInputData]:
    """Return the class tree data for ELK."""
    assert isinstance(diagram.target, information.Class)
    data = generic.collector(diagram, no_symbol=True)
    all_associations: cabc.Iterable[
        information.Association
    ] = diagram._model.search("Association")
    _set_layout_options(data, params)
    processor = ClassProcessor(data, all_associations)
    processor._set_data_types_and_labels(data["children"][0], diagram.target)
    for _, cls in get_all_classes(diagram.target):
        processor.process_class(cls, params)

    legend = makers.make_diagram(diagram)
    legend["layoutOptions"] = copy.deepcopy(_elkjs.RECT_PACKING_LAYOUT_OPTIONS)  # type: ignore[arg-type]
    legend["children"] = processor.legend_boxes
    return data, legend


def _set_layout_options(
    data: _elkjs.ELKInputData, params: dict[str, t.Any]
) -> None:
    data["layoutOptions"] = {**DEFAULT_LAYOUT_OPTIONS, **params}
    _set_partitioning(data["children"][0], 0, params)


def _set_partitioning(box, partition: int, params: dict[str, t.Any]) -> None:
    if params.get("partitioning", False):
        box["layoutOptions"] = {}
        box["layoutOptions"]["elk.partitioning.partition"] = partition


@dataclasses.dataclass
class ClassInfo:
    """All information needed for a ``Class`` box."""

    source: information.Class
    target: information.Class | None
    prop: information.Property
    partition: int
    multiplicity: tuple[str, str] | None
    generalizes: information.Class | None = None
    primitive: bool = False


def process_property(
    source: information.Class,
    prop: information.Property,
    partition: int,
    classes: dict[str, ClassInfo],
    generalizes: information.Class | None = None,
) -> bool:
    """Process a single property for class information."""
    if not prop.type:
        logger.warning(
            "Property without abstract type found: %r", prop._short_repr_()
        )
        return False

    if not prop.type.xtype.endswith("Class") or prop.type.is_primitive:
        logger.debug("Ignoring non-class property: %r", prop._short_repr_())
        return False

    edge_id = f"{source.uuid} {prop.uuid} {prop.type.uuid}"
    if edge_id not in classes:
        classes[edge_id] = _make_class_info(
            source, prop, partition, generalizes=generalizes
        )
        classes.update(get_all_classes(prop.type, partition, classes))
    return True


def get_all_classes(
    root: information.Class,
    partition: int = 0,
    classes: dict[str, ClassInfo] | None = None,
) -> cabc.Iterator[tuple[str, ClassInfo]]:
    """Yield all classes of the class tree."""
    partition += 1
    classes = classes or {}

    for prop in root.owned_properties:
        process_property(root, prop, partition, classes)

    if root.super and not root.super.is_primitive:
        processed_properties = [
            process_property(
                root.super, prop, partition, classes, generalizes=root
            )
            for prop in root.super.owned_properties
        ]

        if not root.super.owned_properties or any(processed_properties):
            if (edge_id := f"{root.uuid} {root.super.uuid}") not in classes:
                classes[edge_id] = _make_class_info(
                    root.super, None, partition, generalizes=root
                )
                classes.update(get_all_classes(root.super, partition, classes))

    for cls in root.sub:
        if cls.is_primitive:
            continue

        processed_properties = [
            process_property(root, prop, partition, classes, generalizes=cls)
            for prop in cls.owned_properties
        ]

        if not cls.owned_properties or not any(processed_properties):
            if (edge_id := f"{root.uuid} {cls.uuid}") not in classes:
                classes[edge_id] = _make_class_info(
                    root, None, partition, generalizes=cls
                )
                classes.update(get_all_classes(cls, partition, classes))

    yield from classes.items()


def _make_class_info(
    source: information.Class,
    prop: information.Property | None,
    partition: int,
    generalizes: information.Class | None = None,
) -> ClassInfo:
    converter = {math.inf: "*"}
    multiplicity = None
    target = None
    if prop is not None:
        start = converter.get(prop.min_card.value, str(prop.min_card.value))
        end = converter.get(prop.max_card.value, str(prop.max_card.value))
        multiplicity = (start, end)
        target = prop.type

    return ClassInfo(
        source=source,
        target=target,
        prop=prop,
        partition=partition,
        multiplicity=multiplicity,
        generalizes=generalizes,
        primitive=source.is_primitive,
    )


def _get_all_non_edge_properties(
    obj: information.Class, data_types: set[str]
) -> tuple[list[_elkjs.ELKInputLabel], list[_elkjs.ELKInputChild]]:
    layout_options = DATA_TYPE_LABEL_LAYOUT_OPTIONS
    properties: list[_elkjs.ELKInputLabel] = []
    legends: list[_elkjs.ELKInputChild] = []
    for prop in obj.properties:
        if prop.type is None:
            continue

        is_class = isinstance(prop.type, information.Class)
        if is_class and not prop.type.is_primitive:
            continue

        text = _get_property_text(prop)
        label = makers.make_label(text, layout_options=layout_options)
        properties.append(label)

        if prop.type.uuid in data_types:
            continue

        data_types.add(prop.type.uuid)
        is_enum = isinstance(prop.type, information.datatype.Enumeration)
        if not is_enum and not (is_class and prop.type.is_primitive):
            continue

        legend = makers.make_box(prop.type, label_getter=_get_legend_labels)
        legend["layoutOptions"] = {}
        legend["layoutOptions"]["nodeSize.constraints"] = "NODE_LABELS"
        legends.append(legend)
    return properties, legends


def _get_property_text(prop: information.Property) -> str:
    text = f"{prop.name}: {prop.type.name}"
    if prop.min_card.value != "1" or prop.max_card.value != "1":
        text = f"[{prop.min_card.value}..{prop.max_card.value}] {text}"
    return text


def _get_legend_labels(
    obj: information.datatype.Enumeration | information.Class,
) -> cabc.Iterator[makers._LabelBuilder]:
    yield {"text": obj.name, "icon": (0, 0), "layout_options": {}}
    if isinstance(obj, information.datatype.Enumeration):
        labels = [literal.name for literal in obj.literals]
    elif isinstance(obj, information.Class):
        labels = [_get_property_text(prop) for prop in obj.owned_properties]
    else:
        return
    layout_options = DATA_TYPE_LABEL_LAYOUT_OPTIONS
    for label in labels:
        yield {
            "text": label,
            "icon": (0, 0),
            "layout_options": layout_options,
        }
