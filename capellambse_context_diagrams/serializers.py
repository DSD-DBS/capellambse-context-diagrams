# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This submodule provides a serializer that transforms data from an ELK-
layouted diagram [_elkjs.ELKOutputData][capellambse_context_diagrams._elkjs.ELKOutputData]
according to [_elkjs.ELKInputData][capellambse_context_diagrams._elkjs.ELKInputData].
The pre-layouted data was collected with the functions from
[collectors][capellambse_context_diagrams.collectors].
"""
from __future__ import annotations

import logging

from capellambse import diagram

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
        self._cache: dict[str, diagram.Box] = {}

    def make_diagram(self, data: _elkjs.ELKOutputData) -> diagram.Diagram:
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
            self._diagram.name, styleclass=self._diagram.styleclass
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
        element: diagram.Box | diagram.Edge
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
            element = diagram.Box(
                ref,
                size,
                uuid=child["id"],
                parent=parent,
                port=is_port,
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
            )
            element.JSON_TYPE = box_type
            self.diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "edge":
            element = diagram.Edge(
                [
                    ref + (point["x"], point["y"])
                    for point in child["routingPoints"]
                ],
                uuid=child["id"],
                source=self.diagram[child["sourceId"]],
                target=self.diagram[child["targetId"]],
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
            )
            self.diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "label":
            assert parent is not None
            if isinstance(parent, diagram.Box) and not parent.port:
                if parent.JSON_TYPE != "symbol":
                    parent.label = child["text"]
                else:
                    parent.label = diagram.Box(
                        ref + (child["position"]["x"], child["position"]["y"]),
                        (child["size"]["width"], child["size"]["height"]),
                        label=child["text"],
                        # parent=parent,
                    )
            else:
                assert isinstance(parent, diagram.Edge)
                parent.labels = [
                    diagram.Box(
                        ref + (child["position"]["x"], child["position"]["y"]),
                        (child["size"]["width"], child["size"]["height"]),
                        label=child["text"],
                        styleoverrides=self.get_styleoverrides(child),
                    )
                ]

            element = parent
        elif child["type"] == "junction":
            uuid = child["id"].split("_", maxsplit=1)[0]
            pos = diagram.Vector2D(**child["position"])
            if self._is_hierarchical(uuid):
                pos += self.diagram[self._diagram.target.uuid].pos

            element = diagram.Circle(
                pos,
                5,
                uuid=child["id"],
                styleclass=self.get_styleclass(uuid),
                styleoverrides=self.get_styleoverrides(child),
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
    ) -> diagram.StyleOverrides | None:
        """Return
        [`styling.CSSStyles`][capellambse_context_diagrams.styling.CSSStyles]
        from a given
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild].
        """
        style_condition = self._diagram.render_styles.get(child["type"])
        styleoverrides = None
        if style_condition is not None:
            if child["type"] != "junction":
                obj = self._diagram._model.by_uuid(child["id"])
            else:
                obj = None

            styleoverrides = style_condition(obj, self)
        return styleoverrides

    def order_children(self) -> None:
        """Reorder diagram elements such that symbols are drawn last."""
        new_diagram = diagram.Diagram(
            self.diagram.name, styleclass=self.diagram.styleclass
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
