# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Serialize an ELK diagram into a capellambse diagram.

This submodule provides a serializer that transforms data from an ELK-
layouted diagram
[_elkjs.ELKOutputData][capellambse_context_diagrams._elkjs.ELKOutputData]
according to
[_elkjs.ELKInputData][capellambse_context_diagrams._elkjs.ELKInputData].

The pre-layouted data was collected with the functions from
[collectors][capellambse_context_diagrams.collectors].
"""

from __future__ import annotations

import collections.abc as cabc
import itertools
import logging
import typing as t

from capellambse import diagram as cdiagram
from capellambse import model as m
from capellambse.svg import decorations

from . import _elkjs, context
from .collectors import makers

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
EdgeContext = tuple[
    _elkjs.ELKOutputEdge,
    cdiagram.Vector2D,
    cdiagram.DiagramElement | None,
]

REMAP_STYLECLASS: dict[t.Any, str | None] = {"Unset": "Association"}


class DiagramSerializer:
    """Serialize an ``elk_diagram`` into a capellambse diagram.

    Attributes
    ----------
    model
        The [`MelodyModel`][capellambse.model.MelodyModel] instance.
    diagram
        The created [`diagram.Diagram`][capellambse.diagram.Diagram]
        instance.
    """

    diagram: cdiagram.Diagram

    def __init__(self, elk_diagram: context.ContextDiagram) -> None:
        self.model = elk_diagram.target._model
        self._diagram = elk_diagram
        self._cache: dict[str, cdiagram.DiagramElement] = {}
        self._edges: dict[str, EdgeContext] = {}
        self._junctions: dict[str, EdgeContext] = {}

    def make_diagram(
        self, data: _elkjs.ELKOutputData, **params: t.Any
    ) -> cdiagram.Diagram:
        """Transform a layouted diagram into a `diagram.Diagram`.

        Parameters
        ----------
        data
            The diagram, including layouting information.
        params
            Additional parameters for the diagram.

        Returns
        -------
        diagram
            A [`diagram.Diagram`][capellambse.diagram.Diagram] constructed
            from the input data.
        """
        self.diagram = cdiagram.Diagram(
            self._diagram.name.replace("/", "\\"),
            styleclass=self._diagram.styleclass,
            params=params,
        )
        for child in data.children:
            self.deserialize_child(child, cdiagram.Vector2D(), None)

        for edge, ref, parent in self._edges.values():
            self.deserialize_child(edge, ref, parent)

        for junction, ref, parent in self._junctions.values():
            self.deserialize_child(junction, ref, parent)

        self.diagram.calculate_viewport()
        self.order_children()
        self._edges.clear()
        self._junctions.clear()
        return self.diagram

    def deserialize_child(
        self,
        child: _elkjs.ELKOutputChild,
        ref: cdiagram.Vector2D,
        parent: cdiagram.DiagramElement | None,
    ) -> None:
        """Convert a `child` into aird elements and adds it to the diagram.

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
        uuid: str
        styleclass: str | None
        derived = False
        if child.id.startswith("__"):
            if ":" in child.id:
                styleclass, uuid = child.id[2:].split(":", 1)
            else:
                styleclass = uuid = child.id[2:]
            if styleclass.startswith("Derived-"):
                styleclass = styleclass.removeprefix("Derived-")
                derived = True
        else:
            styleclass = self.get_styleclass(child.id)
            uuid = child.id

        styleoverrides = self.get_styleoverrides(uuid, child, derived=derived)
        element: cdiagram.Box | cdiagram.Edge | cdiagram.Circle
        if child.type in {"node", "port"}:
            assert parent is None or isinstance(parent, cdiagram.Box)
            has_symbol_cls = makers.is_symbol(styleclass)
            is_port = child.type == "port"
            box_type = ("box", "symbol")[
                is_port
                or (
                    has_symbol_cls
                    and self._diagram.target.uuid != uuid
                    and not self._diagram._display_symbols_as_boxes
                )
            ]

            assert not isinstance(
                child, _elkjs.ELKOutputEdge | _elkjs.ELKOutputJunction
            )
            ref += (child.position.x, child.position.y)
            size = (child.size.width, child.size.height)
            features = []
            if styleclass in decorations.needs_feature_line:
                assert isinstance(child, _elkjs.ELKOutputNode)
                features = handle_features(child)

            element = cdiagram.Box(
                ref,
                size,
                uuid=uuid,
                parent=parent,
                port=is_port,
                styleclass=styleclass,
                styleoverrides=styleoverrides,
                features=features,
                context=getattr(child, "context", {}),
            )
            element.JSON_TYPE = box_type
            self.diagram.add_element(element)
            self._cache[uuid] = element
        elif child.type == "edge":
            styleclass = getattr(child, "styleClass", styleclass)
            styleclass = REMAP_STYLECLASS.get(styleclass, styleclass)
            EDGE_HANDLER.get(styleclass, lambda c: c)(child)

            source_id = child.sourceId
            if source_id.startswith("__"):
                source_id = source_id[2:].split(":", 1)[-1]

            target_id = child.targetId
            if target_id.startswith("__"):
                target_id = target_id[2:].split(":", 1)[-1]

            if child.routingPoints:
                refpoints = [
                    ref + (point.x, point.y) for point in child.routingPoints
                ]
            else:
                source = self._cache[source_id]
                target = self._cache[target_id]
                assert isinstance(source, cdiagram.Box)
                assert isinstance(target, cdiagram.Box)
                refpoints = route_shortest_connection(source, target)

            element = cdiagram.Edge(
                refpoints,
                uuid=child.id,
                source=self.diagram[source_id],
                target=self.diagram[target_id],
                styleclass=styleclass,
                styleoverrides=styleoverrides,
                context=getattr(child, "context", {}),
            )
            self.diagram.add_element(element)
            self._cache[uuid] = element
        elif child.type == "label":
            assert parent is not None
            if parent.JSON_TYPE != "symbol":
                parent.styleoverrides.update(styleoverrides)

            if isinstance(parent, cdiagram.Box):
                attr_name = "floating_labels"
            else:
                attr_name = "labels"

            if (
                parent.port
                and self._diagram._port_label_position
                == _elkjs.PORT_LABEL_POSITION.OUTSIDE.name
            ):
                bring_labels_closer_to_port(child)

            if labels := getattr(parent, attr_name):
                label_box = labels[-1]
                label_box.label += " " + child.text
                label_box.size = cdiagram.Vector2D(
                    max(label_box.size.x, child.size.width),
                    label_box.size.y + child.size.height,
                )
                label_box.pos = cdiagram.Vector2D(
                    min(label_box.pos.x, ref.x + child.position.x),
                    label_box.pos.y,
                )
            else:
                labels.append(
                    cdiagram.Box(
                        ref + (child.position.x, child.position.y),
                        (child.size.width, child.size.height),
                        label=child.text,
                        styleoverrides=styleoverrides,
                    )
                )

            element = parent
        elif child.type == "junction":
            uuid = uuid.rsplit("_", maxsplit=1)[0]
            pos = cdiagram.Vector2D(child.position.x, child.position.y)
            element = cdiagram.Circle(
                ref + pos,
                5,
                uuid=child.id,
                styleclass=self.get_styleclass(uuid),
                styleoverrides=styleoverrides,
                context=getattr(child, "context", {}),
            )
            self.diagram.add_element(element)
            self._cache[uuid] = element
        else:
            logger.warning("Received unknown type %s", child.type)
            return

        for i in getattr(child, "children", []):
            if i.type == "edge":
                self._edges.setdefault(i.id, (i, ref, parent))
            elif i.type == "junction":
                self._junctions.setdefault(i.id, (i, ref, parent))
            else:
                self.deserialize_child(i, ref, element)

    def get_styleclass(self, uuid: str) -> str | None:
        """Return the style-class string from a given ``uuid``."""
        try:
            melodyobj: m.ModelElement | m.Diagram = (
                self._diagram._model.by_uuid(uuid)
            )
        except KeyError:
            if not uuid.startswith("__"):
                return None
            return uuid[2:].split(":", 1)[0]
        else:
            if isinstance(melodyobj, m.Diagram):
                return melodyobj.type.value
            return melodyobj._get_styleclass()

    def get_styleoverrides(
        self, uuid: str, child: _elkjs.ELKOutputChild, *, derived: bool = False
    ) -> cdiagram.StyleOverrides:
        """Return css style overrides from a given ``child``.

        See Also
        --------
        [`styling.CSSStyles`][capellambse_context_diagrams.styling.CSSStyles] :
            A dictionary with CSS styles.
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild] :
            An ELK output child.
        """
        style_condition = self._diagram.render_styles.get(child.type)
        styleoverrides: cdiagram.StyleOverrides = {}
        if style_condition is not None:
            if child.type != "junction":
                obj = self._diagram._model.by_uuid(uuid)
            else:
                obj = None

            styleoverrides = style_condition(obj, self) or {}

        if uuid == self._diagram.target.uuid:
            styleoverrides["stroke-width"] = "4"

        if derived:
            styleoverrides["stroke-dasharray"] = "4"

        style: dict[str, t.Any]
        if style := child.style:
            styleoverrides.update(style)
        return styleoverrides

    def order_children(self) -> None:
        """Reorder diagram elements such that symbols are drawn last."""
        new_diagram = cdiagram.Diagram(
            self.diagram.name,
            styleclass=self.diagram.styleclass,
            params=self.diagram.params,
        )
        draw_last = list[cdiagram.DiagramElement]()
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
    if len(child.children) <= 1:
        return features

    all_labels = [i for i in child.children if i.type == "label"]
    labels = list(itertools.takewhile(lambda i: i.text, all_labels))
    features = [i.text for i in all_labels[len(labels) + 1 :]]
    child.children = labels  # type: ignore[assignment]
    return features


def route_shortest_connection(
    source: cdiagram.Box, target: cdiagram.Box
) -> list[cdiagram.Vector2D]:
    """Calculate shortest path between boxes with 'Oblique' style.

    Calculate the intersection points of the line from source.center to
    target.center with the bounding boxes of the source and target.
    """
    line_start = source.center
    line_end = target.center

    source_intersection = source.vector_snap(
        line_start, source=line_end, style=cdiagram.RoutingStyle.OBLIQUE
    )
    target_intersection = target.vector_snap(
        line_end, source=line_start, style=cdiagram.RoutingStyle.OBLIQUE
    )
    return [source_intersection, target_intersection]


def reverse_edge_refpoints(child: _elkjs.ELKOutputEdge) -> None:
    source = child.sourceId
    target = child.targetId
    child.targetId = source
    child.sourceId = target
    child.routingPoints = child.routingPoints[::-1]


def bring_labels_closer_to_port(child: _elkjs.ELKOutputLabel) -> None:
    """Move labels closer to the port."""
    if child.position.x > 1:
        child.position.x = -5

    if child.position.x < -11:
        child.position.x += 18


EDGE_HANDLER: dict[str | None, cabc.Callable[[_elkjs.ELKOutputEdge], None]] = {
    "Generalization": reverse_edge_refpoints
}
