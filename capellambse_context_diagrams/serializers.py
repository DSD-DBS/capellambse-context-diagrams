# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This submodule provides a serializer that transforms data from an ELK-
layouted diagram [_elkjs.ELKOutputData][capellambse_context_diagrams._elkjs.ELKOutputData]
according to [_elkjs.ELKInputData][capellambse_context_diagrams._elkjs.ELKInputData].
The pre-layouted data was collected with the functions from
[collectors][capellambse_context_diagrams.collectors].
"""
from __future__ import annotations

import collections.abc as cabc
import logging
import typing as t

from capellambse import diagram
from capellambse.svg import decorations

from . import _elkjs, collectors, context

logger = logging.getLogger(__name__)

ElkChildType = str
"""
Elk types can be one of the following types:
* `graph`
* `node`
* `port`
* `label`
* `edge`
* `junction`.
"""

REMAP_STYLECLASS: dict[str, str] = {"Unset": "Association"}


class DiagramSerializer:
    """Serialize an ``elk_diagram`` into an
    [`diagram.Diagram`][capellambse.diagram.Diagram].

    Attributes
    ----------
    model
        The [`MelodyModel`][capellambse.model.MelodyModel] instance.
    diagram
        The created [`diagram.Diagram`][capellambse.diagram.Diagram]
        instance.
    """

    diagram: diagram.Diagram

    def __init__(self, elk_diagram: context.ContextDiagram) -> None:
        self.model = elk_diagram.target._model
        self._diagram = elk_diagram
        self._cache: dict[str, diagram.Box | diagram.Edge] = {}

    def make_diagram(
        self,
        data: _elkjs.ELKOutputData,
        **kwargs: dict[str, t.Any],
    ) -> diagram.Diagram:
        """Transform a layouted diagram into an `diagram.Diagram`.

        Parameters
        ----------
        data
            The diagram, including layouting information.

        Returns
        -------
        diagram
            A [`diagram.Diagram`][capellambse.diagram.Diagram] constructed
            from the input data.
        """
        self.diagram = diagram.Diagram(
            self._diagram.name.replace("/", "\\"),
            styleclass=self._diagram.styleclass,
            params=kwargs,
        )
        for child in data["children"]:
            self.deserialize_child(child, diagram.Vector2D(), None)

        self.diagram.calculate_viewport()
        self.order_children()
        return self.diagram

    def deserialize_child(
        self,
        child: _elkjs.ELKOutputChild,
        ref: diagram.Vector2D,
        parent: diagram.Box | diagram.Edge | None,
    ) -> None:
        """Converts a `child` into aird elements and adds it to the
        diagram.

        Parameters
        ----------
        child
            The child to deserialize.
        ref
            The reference point of the child.
        parent
            The parent of the child. This is either a box or an edge.

        See Also
        --------
        [`diagram.Box`][capellambse.diagram.Box] : Box class type.
        [`diagram.Edge`][capellambse.diagram.Edge] : Edge class type.
        [`diagram.Circle`][capellambse.diagram.Circle] : Circle class
            type.
        [`diagram.Diagram`][capellambse.diagram.Diagram] : Diagram
            class type that stores all previously named classes.
        """
        styleclass: str | None = self.get_styleclass(child["id"])
        element: diagram.Box | diagram.Edge | diagram.Circle
        if child["type"] in {"node", "port"}:
            assert parent is None or isinstance(parent, diagram.Box)
            has_symbol_cls = False
            try:
                obj = self.model.by_uuid(child["id"])
                has_symbol_cls = collectors.makers.is_symbol(obj)
            except KeyError:
                logger.error(
                    "ModelObject could not be found: '%s'", child["id"]
                )

            is_port = child["type"] == "port"
            box_type = ("box", "symbol")[
                is_port
                or has_symbol_cls
                and not self._diagram.target == obj
                and not self._diagram.display_symbols_as_boxes
            ]

            ref += (child["position"]["x"], child["position"]["y"])  # type: ignore
            size = (child["size"]["width"], child["size"]["height"])  # type: ignore
            features = []
            if styleclass in decorations.needs_feature_line:
                features = handle_features(child)  # type: ignore[arg-type]

            element = diagram.Box(
                ref,
                size,
                uuid=child["id"],
                parent=parent,
                port=is_port,
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
                features=features,
                context=child.get("context"),
            )
            element.JSON_TYPE = box_type
            self.diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "edge":
            styleclass = child.get("styleclass", styleclass)  # type: ignore[assignment]
            styleclass = REMAP_STYLECLASS.get(styleclass, styleclass)  # type: ignore[arg-type]
            EDGE_HANDLER.get(styleclass, lambda c: c)(child)

            if child["routingPoints"]:
                refpoints = [
                    ref + (point["x"], point["y"])
                    for point in child["routingPoints"]
                ]
            else:
                source = self._cache[child["sourceId"]]
                target = self._cache[child["targetId"]]
                refpoints = route_shortest_connection(source, target)

            element = diagram.Edge(
                refpoints,
                uuid=child["id"],
                source=self.diagram[child["sourceId"]],
                target=self.diagram[child["targetId"]],
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
                context=child.get("context"),
            )
            self.diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "label":
            assert parent is not None
            if not parent.port:
                if parent.JSON_TYPE != "symbol":
                    parent.styleoverrides |= self.get_styleoverrides(child)

                if isinstance(parent, diagram.Box):
                    attr_name = "floating_labels"
                else:
                    attr_name = "labels"

                labels = getattr(parent, attr_name)
                if labels:
                    label_box = labels[-1]
                    label_box.label += " " + child["text"]
                    label_box.size = diagram.Vector2D(
                        max(label_box.size.x, child["size"]["width"]),
                        label_box.size.y + child["size"]["height"],
                    )
                    label_box.pos = diagram.Vector2D(
                        min(label_box.pos.x, ref.x + child["position"]["x"]),
                        label_box.pos.y,
                    )
                else:
                    labels.append(
                        diagram.Box(
                            ref
                            + (child["position"]["x"], child["position"]["y"]),
                            (child["size"]["width"], child["size"]["height"]),
                            label=child["text"],
                            styleoverrides=self.get_styleoverrides(child),
                        )
                    )

            element = parent
        elif child["type"] == "junction":
            uuid = child["id"].split("_", maxsplit=1)[0]
            pos = diagram.Vector2D(**child["position"])
            if self._is_hierarchical(uuid):
                pos += self.diagram[self._diagram.target.uuid].pos

            element = diagram.Circle(
                ref + pos,
                5,
                uuid=child["id"],
                styleclass=self.get_styleclass(uuid),
                styleoverrides=self.get_styleoverrides(child),
                context=child.get("context"),
            )
            self.diagram.add_element(element)
        else:
            logger.warning("Received unknown type %s", child["type"])
            return

        for i in child.get("children", []):  # type: ignore
            self.deserialize_child(i, ref, element)

    def _is_hierarchical(self, uuid: str) -> bool:
        def is_contained(obj: diagram.Box) -> bool:
            if obj.port and obj.parent and obj.parent.parent:
                parent = obj.parent.parent
            else:
                parent = obj.parent

            return parent.uuid == self._diagram.target.uuid

        exchange = self.diagram[uuid]
        return is_contained(exchange.source) and is_contained(exchange.target)

    def get_styleclass(self, uuid: str) -> str | None:
        """Return the style-class string from a given
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild].
        """
        styleclass: str | None
        try:
            melodyobj = self._diagram._model.by_uuid(uuid)
            styleclass = diagram.get_styleclass(melodyobj)
        except KeyError:
            styleclass = None
        return styleclass

    def get_styleoverrides(
        self, child: _elkjs.ELKOutputChild
    ) -> diagram.StyleOverrides:
        """Return
        [`styling.CSSStyles`][capellambse_context_diagrams.styling.CSSStyles]
        from a given
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild].
        """
        style_condition = self._diagram.render_styles.get(child["type"])
        styleoverrides: dict[str, t.Any] = {}
        if style_condition is not None:
            if child["type"] != "junction":
                obj = self._diagram._model.by_uuid(child["id"])
            else:
                obj = None

            styleoverrides = style_condition(obj, self) or {}

        style: dict[str, t.Any]
        if style := child.get("style", {}):
            styleoverrides |= style
        return styleoverrides

    def order_children(self) -> None:
        """Reorder diagram elements such that symbols are drawn last."""
        new_diagram = diagram.Diagram(
            self.diagram.name,
            styleclass=self.diagram.styleclass,
            params=self.diagram.params,
        )
        draw_last = list[diagram.DiagramElement]()
        for element in self.diagram:
            if element.JSON_TYPE in {"symbol", "circle"}:
                draw_last.append(element)
            else:
                new_diagram.add_element(element)

        for element in draw_last:
            new_diagram.add_element(element)

        self.diagram = new_diagram


def handle_features(child: _elkjs.ELKOutputNode) -> list[str]:
    """Return all consecutive labels (without first) from the ``child``."""
    features: list[str] = []
    if len(child["children"]) <= 1:
        return features

    for c in child["children"][1:]:
        if not c["type"] == "label":
            continue
        features.append(c["text"])
    child["children"] = child["children"][:1]
    return features


def route_shortest_connection(
    source: diagram.Box,
    target: diagram.Box,
) -> list[diagram.Vector2D]:
    """Calculate shortest path between boxes with 'Oblique' style.

    Calculate the intersection points of the line from source.center to
    target.center with the bounding boxes of the source and target.
    """
    line_start = source.center
    line_end = target.center

    source_intersection = source.vector_snap(
        line_start, source=line_end, style=diagram.RoutingStyle.OBLIQUE
    )
    target_intersection = target.vector_snap(
        line_end, source=line_start, style=diagram.RoutingStyle.OBLIQUE
    )
    return [source_intersection, target_intersection]


def reverse_edge_refpoints(child: _elkjs.ELKOutputEdge) -> None:
    source = child["sourceId"]
    target = child["targetId"]
    child["targetId"] = source
    child["sourceId"] = target
    child["routingPoints"] = child["routingPoints"][::-1]


EDGE_HANDLER: dict[str, cabc.Callable[[_elkjs.ELKOutputEdge], None]] = {
    "Generalization": reverse_edge_refpoints
}
