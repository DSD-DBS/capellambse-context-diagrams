# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""This submodule defines the collector for the Class-Tree diagram."""
from __future__ import annotations

import collections.abc as cabc
import typing as t

from capellambse import helpers
from capellambse.model.crosslayer import information

from .. import _elkjs, context
from . import generic, makers

LAYOUT_OPTIONS: _elkjs.LayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.direction": "DOWN",
    "partitioning.activate": True,
    "edgeLabels.sideSelection": "ALWAYS_DOWN",
}


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """Return the class tree data for ELK."""
    assert isinstance(diagram.target, information.Class)
    data = generic.collector(diagram, no_symbol=True)
    data["children"][0]["layoutOptions"] = {}
    data["children"][0]["layoutOptions"]["elk.partitioning.partition"] = 0
    data["layoutOptions"] = LAYOUT_OPTIONS
    data["layoutOptions"]["algorithm"] = (params or {})["algorithm"]
    data["layoutOptions"]["elk.direction"] = (params or {})["direction"]
    data["layoutOptions"]["edgeRouting"] = (params or {})["edgeRouting"]

    made_boxes: set[str] = set()
    for uid, (source, prop, target) in get_all_classes(diagram.target):
        partition = uid.split(" ")[-1]
        if target.uuid not in made_boxes:
            made_boxes.add(target.uuid)
            box = makers.make_box(target)
            box["layoutOptions"] = {}
            box["layoutOptions"]["elk.partitioning.partition"] = int(partition)
            data["children"].append(box)

        width, height = helpers.extent_func(prop.name)
        label: _elkjs.ELKInputLabel = {
            "text": prop.name,
            "width": width + 2 * makers.LABEL_HPAD,
            "height": height + 2 * makers.LABEL_VPAD,
        }
        data["edges"].append(
            {
                "id": prop.uuid,
                "sources": [source.uuid],
                "targets": [target.uuid],
                "labels": [label],
            }
        )
    return data


ClassContext = tuple[
    information.Class, information.Property, information.Class
]


def get_all_classes(
    root: information.Class, partition: int = 0
) -> cabc.Iterator[tuple[str, ClassContext]]:
    """Yield all classes of the class tree."""
    partition += 1
    classes: dict[str, ClassContext] = {}
    for prop in root.properties:
        if prop.type.xtype.endswith("Class"):
            edge_id = f"{root.name} {prop.type.name} {partition}"
            if edge_id not in classes:
                classes[edge_id] = (root, prop, prop.type)
                classes.update(dict(get_all_classes(prop.type, partition)))

    yield from classes.items()
