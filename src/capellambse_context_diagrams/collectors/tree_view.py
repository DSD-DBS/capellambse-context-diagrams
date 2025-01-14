# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the Class-Tree diagram."""

from __future__ import annotations

import collections
import collections.abc as cabc
import copy
import dataclasses
import logging
import math
import typing as t

import capellambse.model as m
from capellambse.metamodel import information, modeltypes

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
    def __init__(self, data: _elkjs.ELKInputData) -> None:
        self.data = data
        self.made_boxes: set[str] = {data.children[0].id}
        self.made_edges: set[str] = set()
        self.data_types: set[str] = set()
        self.legend_boxes: list[_elkjs.ELKInputChild] = []

        self._edge_count: dict[str, int] = collections.defaultdict(int)

    def __contains__(self, uuid: str) -> bool:
        objects = self.data.children + self.data.edges  # type: ignore[operator]
        return uuid in {obj.id for obj in objects}

    def process_class(self, cls: ClassInfo, params: dict[str, t.Any]):
        self._process_box(cls.source, cls.partition, params)

        if not cls.primitive and isinstance(cls.target, information.Class):
            assert cls.prop is not None
            self._process_box(cls.target, cls.partition, params)

            if cls.prop.association is not None:
                edge_id = cls.prop.association.uuid
            else:
                logger.warning(
                    "No Association found for %s set on 'navigable_members'",
                    cls.prop._short_repr_(),
                )
                if cls.prop.kind != modeltypes.AggregationKind.UNSET:
                    styleclass = cls.prop.kind.name.capitalize()
                else:
                    styleclass = "Association"

                self._edge_count[cls.prop.uuid] += 1
                i = self._edge_count[cls.prop.uuid]
                edge_id = f"__{styleclass}:{cls.prop.uuid}-{i}"

            if edge_id not in self.made_edges:
                self.made_edges.add(edge_id)
                text = cls.prop.name if cls.prop else ""
                if cls.multiplicity is None:
                    start = end = "1"
                else:
                    start, end = cls.multiplicity

                if start != "1" or end != "1":
                    text = f"[{start}..{end}] {text}"

                self.data.edges.append(
                    _elkjs.ELKInputEdge(
                        id=edge_id,
                        sources=[cls.source.uuid],
                        targets=[cls.target.uuid],
                        labels=makers.make_label(text),
                    )
                )

        if cls.generalizes:
            self._process_box(cls.generalizes, cls.partition, params)
            edge = cls.generalizes.generalizations.by_super(
                cls.source, single=True
            )
            if edge.uuid not in self.made_edges:
                self.made_edges.add(edge.uuid)
                self.data.edges.append(
                    _elkjs.ELKInputEdge(
                        id=edge.uuid,
                        sources=[cls.source.uuid],
                        targets=[cls.generalizes.uuid],
                    )
                )

    def _process_box(
        self,
        obj: information.Class,
        partition: int,
        params: dict[str, t.Any],
    ) -> None:
        if obj.uuid not in self.made_boxes:
            self._make_box(obj, partition, params)

    def _make_box(
        self,
        obj: information.Class,
        partition: int,
        params: dict[str, t.Any],
    ) -> _elkjs.ELKInputChild:
        self.made_boxes.add(obj.uuid)
        box = makers.make_box(
            obj,
            layout_options=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
        )
        self._set_data_types_and_labels(box, obj)
        _set_partitioning(box, partition, params)
        self.data.children.append(box)
        return box

    def _set_data_types_and_labels(
        self, box: _elkjs.ELKInputChild, target: information.Class
    ) -> None:
        properties, legends = _get_all_non_edge_properties(
            target, self.data_types
        )
        box.labels.extend(properties)
        box.width, box.height = makers.calculate_height_and_width(
            list(box.labels)
        )
        for legend in legends:
            if legend.id not in self:
                self.legend_boxes.append(legend)


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> tuple[_elkjs.ELKInputData, _elkjs.ELKInputData]:
    """Return the class tree data for ELK."""
    assert isinstance(diagram.target, information.Class)
    data = generic.collector(diagram, no_symbol=True)
    data.children[0].labels[0].layoutOptions.update(
        makers.DEFAULT_LABEL_LAYOUT_OPTIONS
    )
    _set_layout_options(data, params)
    processor = ClassProcessor(data)
    processor._set_data_types_and_labels(data.children[0], diagram.target)
    for _, cls in get_all_classes(
        diagram.target,
        max_partition=params.get("depth"),
        super=params.get("super", "ROOT"),
        sub=params.get("sub", "ROOT"),
    ):
        processor.process_class(cls, params)

    legend = makers.make_diagram(diagram)
    legend.layoutOptions = copy.deepcopy(_elkjs.RECT_PACKING_LAYOUT_OPTIONS)  # type: ignore[arg-type]
    legend.children = processor.legend_boxes
    return data, legend


def _set_layout_options(
    data: _elkjs.ELKInputData, params: dict[str, t.Any]
) -> None:
    options = {
        k: v for k, v in params.items() if k not in ("depth", "super", "sub")
    }
    data.layoutOptions = {**DEFAULT_LAYOUT_OPTIONS, **options}
    _set_partitioning(data.children[0], 0, params)


def _set_partitioning(
    box: _elkjs.ELKInputChild, partition: int, params: dict[str, t.Any]
) -> None:
    if params.get("partitioning", False):
        box.layoutOptions = {}
        box.layoutOptions["elk.partitioning.partition"] = partition


@dataclasses.dataclass
class ClassInfo:
    """All information needed for a ``Class`` box."""

    source: information.Class
    target: information.Class | None
    prop: information.Property | None
    partition: int
    multiplicity: tuple[str, str] | None
    generalizes: information.Class | None = None
    primitive: bool = False


@dataclasses.dataclass
class _PropertyInfo:
    """Builder dataclass for properties."""

    source: information.Class
    prop: information.Property
    partition: int
    classes: dict[str, ClassInfo] = dataclasses.field(default_factory=dict)
    generalizes: information.Class | None = None
    max_partition: int | None = None
    super: t.Literal["ROOT"] | t.Literal["ALL"] = "ALL"
    sub: t.Literal["ROOT"] | t.Literal["ALL"] = "ALL"


def process_property(
    property: _PropertyInfo,
) -> None:
    """Process a single property for class information."""
    prop = property.prop
    if not prop.type:
        logger.debug("Ignoring property without type: %s", prop._short_repr_())
        return

    if not prop.type.xtype.endswith("Class") or prop.type.is_primitive:
        logger.debug("Ignoring non-class property: %s", prop._short_repr_())
        return

    if (
        property.max_partition is not None
        and property.partition > property.max_partition
    ):
        return

    edge_id = f"{property.source.uuid} {prop.uuid} {prop.type.uuid}"
    if edge_id not in property.classes:
        property.classes[edge_id] = _make_class_info(
            property.source,
            prop,
            property.partition,
            generalizes=property.generalizes,
        )
        property.classes.update(
            get_all_classes(
                prop.type,
                property.partition,
                property.classes,
                property.max_partition,
                property.super,
                property.sub,
            )
        )


def get_all_classes(
    root: information.Class,
    partition: int = 0,
    classes: dict[str, ClassInfo] | None = None,
    max_partition: int | None = None,
    super: t.Literal["ROOT"] | t.Literal["ALL"] = "ALL",
    sub: t.Literal["ROOT"] | t.Literal["ALL"] = "ALL",
) -> cabc.Iterator[tuple[str, ClassInfo]]:
    """Yield all classes of the class tree."""
    partition += 1
    classes = classes or {}
    if max_partition is not None and partition > max_partition:
        return

    for prop in root.owned_properties:
        property = _PropertyInfo(
            root, prop, partition, classes, None, max_partition, super, sub
        )
        process_property(property)

    if (
        (super == "ALL" or (super == "ROOT" and partition == 1))
        and isinstance(root.super, information.Class)
        and not root.super.is_primitive
    ):
        for prop in root.super.owned_properties:
            process_property(
                _PropertyInfo(
                    root.super,
                    prop,
                    partition + 1,
                    classes,
                    root,
                    max_partition,
                    super,
                    sub,
                )
            )

        if (edge_id := f"{root.uuid} {root.super.uuid}") not in classes:
            classes[edge_id] = _make_class_info(
                root.super,
                None,
                partition,
                generalizes=root,
            )
            classes.update(
                get_all_classes(
                    root.super,
                    partition,
                    classes,
                    max_partition,
                    super,
                    sub,
                )
            )

    if sub == "ALL" or (sub == "ROOT" and partition == 1):
        for cls in root.sub:
            if cls.is_primitive:
                continue

            for prop in cls.owned_properties:
                process_property(
                    _PropertyInfo(
                        cls,
                        prop,
                        partition,
                        classes,
                        None,
                        max_partition,
                        super,
                        sub,
                    )
                )

            if (edge_id := f"{root.uuid} {cls.uuid}") not in classes:
                classes[edge_id] = _make_class_info(
                    root, None, partition, generalizes=cls
                )
                classes.update(
                    get_all_classes(
                        cls, partition, classes, max_partition, super, sub
                    )
                )

    yield from classes.items()


def _make_class_info(
    source: information.Class,
    prop: information.Property | None,
    partition: int,
    generalizes: information.Class | None = None,
) -> ClassInfo:
    multiplicity = None
    target = None
    if prop is not None:
        start = getattr(prop.min_card, "value", "1")
        end = getattr(prop.max_card, "value", "1")
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
    properties = [
        _elkjs.ELKInputLabel(
            text="",
            layoutOptions=makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
            width=0,
            height=0,
        )
    ]
    legends: list[_elkjs.ELKInputChild] = []
    for prop in obj.properties:
        if prop.type is None:
            continue

        is_class = isinstance(prop.type, information.Class)
        if is_class and not prop.type.is_primitive:
            continue

        text = _get_property_text(prop)
        labels = makers.make_label(
            text,
            icon=(makers.ICON_WIDTH, 0),
            layout_options=layout_options,
            max_width=math.inf,
        )
        properties.extend(labels)

        if prop.type.uuid in data_types:
            continue

        data_types.add(prop.type.uuid)
        is_enum = isinstance(prop.type, information.datatype.Enumeration)
        if not is_enum and not (is_class and prop.type.is_primitive):
            continue

        legend = makers.make_box(
            prop.type,
            label_getter=_get_legend_labels,
            max_label_width=math.inf,
        )
        legend.layoutOptions = {}
        legend.layoutOptions["nodeSize.constraints"] = "NODE_LABELS"
        legends.append(legend)
    return properties, legends


def _get_property_text(prop: information.Property) -> str:
    if prop.type is not None:
        text = f"{prop.name}: {prop.type.name}"
    else:
        text = f"{prop.name}: <untyped>"

    min_card = getattr(prop.min_card, "value", "1")
    max_card = getattr(prop.max_card, "value", "1")

    if min_card != "1" or max_card != "1":
        text = f"[{min_card}..{max_card}] {text}"
    return text


def _get_legend_labels(
    obj: m.ModelElement,
) -> cabc.Iterator[makers._LabelBuilder]:
    yield {
        "text": obj.name,
        "icon": (0, 0),
        "layout_options": makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
    }
    yield {
        "text": "",
        "icon": (0, 0),
        "layout_options": makers.DEFAULT_LABEL_LAYOUT_OPTIONS,
    }
    if isinstance(obj, information.datatype.Enumeration):
        labels = [literal.name for literal in obj.literals]
    elif isinstance(obj, information.Class):
        labels = [_get_property_text(prop) for prop in obj.owned_properties]
    else:
        labels = []
    layout_options = DATA_TYPE_LABEL_LAYOUT_OPTIONS
    for label in labels:
        yield {"text": label, "icon": (0, 0), "layout_options": layout_options}
