# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""This submodule defines the collector for the Class-Tree diagram."""
from __future__ import annotations

import collections.abc as cabc
import dataclasses
import math
import typing as t

from capellambse import helpers
from capellambse.model.crosslayer import information

from .. import _elkjs, context
from . import generic, makers


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Return the class tree data for ELK."""
    assert isinstance(diagram.target, information.Class)
    data = generic.collector(diagram, no_symbol=True)
    if params.get("partitioning", False):
        data["layoutOptions"]["partitioning.activate"] = True
        data["children"][0]["layoutOptions"] = {}
        data["children"][0]["layoutOptions"]["elk.partitioning.partition"] = 0

    data["layoutOptions"]["edgeLabels.sideSelection"] = params.get(
        "edgeLabelsSide", "ALWAYS_DOWN"
    )
    data["layoutOptions"]["algorithm"] = params.get("algorithm", "layered")
    data["layoutOptions"]["elk.direction"] = params.get("direction", "DOWN")
    data["layoutOptions"]["edgeRouting"] = params.get(
        "edgeRouting", "ORTHOGONAL"
    )

    made_boxes: set[str] = set()
    for _, cls in get_all_classes(diagram.target):
        if cls.target.uuid not in made_boxes:
            made_boxes.add(cls.target.uuid)
            box = makers.make_box(cls.target)
            if params.get("partitioning", False):
                box["layoutOptions"] = {}
                box["layoutOptions"]["elk.partitioning.partition"] = int(
                    cls.partition
                )
            data["children"].append(box)

        text = cls.prop.name
        start, end = cls.multiplicity
        if start != "1" or end != "1":
            text = f"[{start}..{end}] {text}"

        width, height = helpers.extent_func(text)
        label: _elkjs.ELKInputLabel = {
            "text": text,
            "width": width + 2 * makers.LABEL_HPAD,
            "height": height + 2 * makers.LABEL_VPAD,
        }
        data["edges"].append(
            {
                "id": cls.prop.uuid,
                "sources": [cls.source.uuid],
                "targets": [cls.target.uuid],
                "labels": [label],
            }
        )
    return data


@dataclasses.dataclass
class ClassInfo:
    source: information.Class
    target: information.Class
    prop: information.Property
    partition: int
    multiplicity: tuple[str, str]


def get_all_classes(
    root: information.Class, partition: int = 0
) -> cabc.Iterator[tuple[str, ClassInfo]]:
    """Yield all classes of the class tree."""
    partition += 1
    visited_classes = set()
    classes: dict[str, ClassInfo] = {}
    for prop in root.properties:
        if prop.type.xtype.endswith("Class"):
            if prop.uuid in visited_classes:
                continue
            visited_classes.add(prop.uuid)

            edge_id = f"{root.uuid} {prop.uuid} {prop.type.uuid}"
            if edge_id not in classes:
                classes[edge_id] = _make_class_info(root, prop, partition)
                classes.update(dict(get_all_classes(prop.type, partition)))
    yield from classes.items()


def _make_class_info(
    source: information.Class, prop: information.Property, partition: int
) -> ClassInfo:
    converter = {math.inf: "*"}
    start = converter.get(prop.min_card.value, str(prop.min_card.value))
    end = converter.get(prop.max_card.value, str(prop.max_card.value))
    return ClassInfo(
        source=source,
        target=prop.type,
        prop=prop,
        partition=partition,
        multiplicity=(start, end),
    )
