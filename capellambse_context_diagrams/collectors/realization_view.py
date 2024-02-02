# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This submodule defines the collector for the RealizationView diagram."""
from __future__ import annotations

import collections.abc as cabc
import copy
import re
import typing as t

from capellambse.model import common, crosslayer
from capellambse.model.crosslayer import cs, fa

from .. import _elkjs, context
from . import makers

RE_LAYER_PTRN = re.compile(r"([A-Z]?[a-z]+)")


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> tuple[_elkjs.ELKInputData, list[_elkjs.ELKInputEdge]]:
    """Return the class tree data for ELK."""
    data = makers.make_diagram(diagram)
    layout_options: _elkjs.LayoutOptions = copy.deepcopy(
        _elkjs.RECT_PACKING_LAYOUT_OPTIONS  # type:ignore[arg-type]
    )
    layout_options["elk.contentAlignment"] = "V_CENTER H_CENTER"
    del layout_options["widthApproximation.targetWidth"]
    data["layoutOptions"] = layout_options
    _collector = COLLECTORS[params.get("search_direction", "ALL")]
    lay_to_els = _collector(diagram.target, params.get("depth", 1))
    layer_layout_options: _elkjs.LayoutOptions = layout_options | {  # type: ignore[operator]
        "nodeSize.constraints": "[NODE_LABELS,MINIMUM_SIZE]",
    }  # type: ignore[assignment]
    edges: list[_elkjs.ELKInputEdge] = []
    for layer in ("Operational", "System", "Logical", "Physical"):
        if not (elements := lay_to_els.get(layer)):  # type: ignore[call-overload]
            continue

        labels = [makers.make_label(layer)]
        width, height = makers.calculate_height_and_width(labels)
        layer_box: _elkjs.ELKInputChild = {
            "id": elements[0]["layer"].uuid,
            "children": [],
            "height": width,
            "width": height,
            "layoutOptions": layer_layout_options,
        }
        children: dict[str, _elkjs.ELKInputChild] = {}
        for elt in elements:
            assert elt["element"] is not None
            if elt["origin"] is not None:
                edges.append(
                    {
                        "id": f'{elt["origin"].uuid}_{elt["element"].uuid}',
                        "sources": [elt["origin"].uuid],
                        "targets": [elt["element"].uuid],
                    }
                )

            if elt.get("reverse", False):
                source = elt["element"]
                target = elt["origin"]
            else:
                source = elt["origin"]
                target = elt["element"]

            if not (element_box := children.get(target.uuid)):
                element_box = makers.make_box(target, no_symbol=True)
                children[target.uuid] = element_box
                layer_box["children"].append(element_box)
                index = len(layer_box["children"]) - 1

                if params.get("show_owners"):
                    owner = target.owner
                    if not isinstance(owner, (fa.Function, cs.Component)):
                        continue

                    if not (owner_box := children.get(owner.uuid)):
                        owner_box = makers.make_box(owner, no_symbol=True)
                        owner_box["height"] += element_box["height"]
                        children[owner.uuid] = owner_box
                        layer_box["children"].append(owner_box)

                    del layer_box["children"][index]
                    owner_box.setdefault("children", []).append(element_box)
                    owner_box["width"] += element_box["width"]
                    if (
                        source is not None
                        and source.owner.uuid in children
                        and owner.uuid in children
                    ):
                        eid = f"{source.owner.uuid}_{owner.uuid}"
                        edges.append(
                            {
                                "id": eid,
                                "sources": [source.owner.uuid],
                                "targets": [owner.uuid],
                            }
                        )

        data["children"].append(layer_box)
    return data, edges


def collect_realized(
    start: common.GenericElement, depth: int
) -> dict[LayerLiteral, list[dict[str, t.Any]]]:
    """Collect all elements from ``realized_`` attributes up to depth."""
    return collect_elements(start, depth, "ABOVE", "realized")


def collect_realizing(
    start: common.GenericElement, depth: int
) -> dict[LayerLiteral, list[dict[str, t.Any]]]:
    """Collect all elements from ``realizing_`` attributes down to depth."""
    return collect_elements(start, depth, "BELOW", "realizing")


def collect_all(
    start: common.GenericElement, depth: int
) -> dict[LayerLiteral, list[dict[str, t.Any]]]:
    """Collect all elements in both ABOVE and BELOW directions."""
    above = collect_realized(start, depth)
    below = collect_realizing(start, depth)
    return above | below


def collect_elements(
    start: common.GenericElement,
    depth: int,
    direction: str,
    attribute_prefix: str,
    origin: common.GenericElement | None = None,
) -> dict[LayerLiteral, list[dict[str, t.Any]]]:
    """Collect elements based on the specified direction and attribute name."""
    layer_obj, layer = find_layer(start)
    collected_elements: dict[LayerLiteral, list[dict[str, t.Any]]] = {}
    if direction == "ABOVE" or origin is None:
        collected_elements = {
            layer: [{"element": start, "origin": origin, "layer": layer_obj}]
        }
    elif direction == "BELOW" and origin is not None:
        collected_elements = {
            layer: [
                {
                    "element": origin,
                    "origin": start,
                    "layer": layer_obj,
                    "reverse": True,
                }
            ]
        }

    if (
        (direction == "ABOVE" and layer == "Operational")
        or (direction == "BELOW" and layer == "Physical")
        or depth == 0
    ):
        return collected_elements

    if isinstance(start, fa.Function):
        attribute_name = f"{attribute_prefix}_functions"
    else:
        assert isinstance(start, cs.Component)
        attribute_name = f"{attribute_prefix}_components"

    for element in getattr(start, attribute_name, []):
        sub_collected = collect_elements(
            element, depth - 1, direction, attribute_prefix, origin=start
        )
        for sub_layer, sub_elements in sub_collected.items():
            collected_elements.setdefault(sub_layer, []).extend(sub_elements)
    return collected_elements


LayerLiteral = t.Union[
    t.Literal["Operational"],
    t.Literal["System"],
    t.Literal["Logical"],
    t.Literal["Physical"],
]


def find_layer(
    obj: common.GenericElement,
) -> tuple[crosslayer.BaseArchitectureLayer, LayerLiteral]:
    """Return the layer object and its literal.

    Return either one of the following:
      * ``Operational``
      * ``System``
      * ``Logical``
      * ``Physical``
    """
    parent = obj
    while not isinstance(parent, crosslayer.BaseArchitectureLayer):
        parent = parent.parent
    if not (match := RE_LAYER_PTRN.match(type(parent).__name__)):
        raise ValueError("No layer was found.")
    return parent, match.group(1)  # type:ignore[return-value]


Collector = cabc.Callable[
    [common.GenericElement, int], dict[LayerLiteral, list[dict[str, t.Any]]]
]
COLLECTORS: dict[str, Collector] = {
    "ALL": collect_all,
    "ABOVE": collect_realized,
    "BELOW": collect_realizing,
}
"""The functions to receive the diagram elements for every layer."""
