# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""This submodule provides a serializer that transform data from an ELK-
layouted diagram [_elkjs.ELKOutputData][capellambse_context_diagrams._elkjs.ELKOutputData]
according to [_elkjs.ELKInputData][capellambse_context_diagrams._elkjs.ELKInputData].
The pre-layouted data was collected with the functions from
[collectors][capellambse_context_diagrams.collectors].
"""
from __future__ import annotations

import logging

from capellambse import aird, helpers
from capellambse.model import common
from capellambse.svg.decorations import icon_padding, icon_size

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
    [`aird.Diagram`][capellambse.aird.diagram.Diagram].

    Attributes
    ----------
    model
        The [`MelodyModel`][capellambse.model.MelodyModel] instance.
    aird_diagram
        The created [`aird.Diagram`][capellambse.aird.diagram.Diagram]
        instance.
    """

    aird_diagram: aird.Diagram

    def __init__(self, elk_diagram: context.ContextDiagram) -> None:
        self.model = elk_diagram.target._model
        self._diagram = elk_diagram
        self._cache: dict[str, aird.Box] = {}

    def make_diagram(self, data: _elkjs.ELKOutputData) -> aird.Diagram:
        """Transform a layouted diagram into an `aird.Diagram`.

        Parameters
        ----------
        data
            The diagram, including layouting information.

        Returns
        -------
        diagram
            A [`aird.Diagram`][capellambse.aird.diagram.Diagram] constructed
            from the input data.
        """
        self.aird_diagram = aird.Diagram(
            self._diagram.name, styleclass=self._diagram.styleclass
        )
        for child in data["children"]:
            self.deserialize_child(child, aird.Vector2D(), None)

        space_checkers = {
            "box": self.check_boxlabel_space,
            "edge": self.check_edgelabel_space,
            "symbol": lambda _: None,  # No need since label is outside
        }
        for element in self._cache.values():
            if not element.port:
                space_checkers[element.JSON_TYPE](element)
            if element.JSON_TYPE != "edge":
                self.check_viewBox_space(element)

        return self.aird_diagram

    def deserialize_child(
        self,
        child: _elkjs.ELKOutputChild,
        ref: aird.Vector2D,
        parent: aird.Box | aird.Edge | None,
    ) -> None:
        """Converts a `child` into aird elements and adds it to the
        diagram.

        Parameters
        ----------
        child : _elkjs.ELKOutputChild
            The child to deserialize.
        ref : aird.Vector2D
            The reference point of the child.
        parent : aird.Box | aird.Edge | None
            The parent of the child. This is either a box or an edge.

        See Also
        --------
        [`aird.Box`][capellambse.aird.diagram.Box] : Box class type.
        [`aird.Edge`][capellambse.aird.diagram.Edge] : Edge class type.
        [`aird.Circle`][capellambse.aird.diagram.Circle] : Circle class
            type.
        [`aird.Diagram`][capellambse.aird.diagram.Diagram] : Diagram
            class type that stores all previously named classes.
        """
        styleclass: str | None = self.get_styleclass(child["id"])
        element: aird.Box | aird.Edge
        if child["type"] in {"node", "port"}:
            assert parent is None or isinstance(parent, aird.Box)
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
            element = aird.Box(
                ref,
                size,
                uuid=child["id"],
                parent=parent,
                port=is_port,
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
            )
            element.JSON_TYPE = box_type
            self.aird_diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "edge":
            element = aird.Edge(
                [
                    ref + (point["x"], point["y"])
                    for point in child["routingPoints"]
                ],
                uuid=child["id"],
                source=self.aird_diagram[child["sourceId"]],
                target=self.aird_diagram[child["targetId"]],
                styleclass=styleclass,
                styleoverrides=self.get_styleoverrides(child),
            )
            self.aird_diagram.add_element(element)
            self._cache[child["id"]] = element
        elif child["type"] == "label":
            assert parent is not None
            if isinstance(parent, aird.Box) and not parent.port:
                if parent.JSON_TYPE != "symbol":
                    parent.label = child["text"]
                else:
                    parent.label = aird.Box(
                        ref + (child["position"]["x"], child["position"]["y"]),
                        (child["size"]["width"], child["size"]["height"]),
                        label=child["text"],
                        # parent=parent,
                    )
            else:
                assert isinstance(parent, aird.Edge)
                parent.labels = [
                    aird.Box(
                        ref + (child["position"]["x"], child["position"]["y"]),
                        (child["size"]["width"], child["size"]["height"]),
                        label=child["text"],
                        styleoverrides=self.get_styleoverrides(child),
                    )
                ]

            element = parent
        elif child["type"] == "junction":
            uuid = child["id"].split("_", maxsplit=1)[0]
            element = aird.Circle(
                aird.Vector2D(**child["position"]),
                5,
                uuid=child["id"],
                styleclass=self.get_styleclass(uuid),
                styleoverrides=self.get_styleoverrides(child),
            )
            self.aird_diagram.add_element(element)
        else:
            logger.warning("Received unknown type %s", child["type"])
            return

        for i in child.get("children", []):  # type: ignore
            self.deserialize_child(i, ref, element)

    def get_styleclass(self, uuid: str) -> str | None:
        """Return the style-class string from a given
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild].
        """
        styleclass: str | None
        try:
            melodyobj = self._diagram._model.by_uuid(uuid)
            styleclass = get_styleclass(melodyobj)
        except KeyError:
            styleclass = None
        return styleclass

    def get_styleoverrides(
        self, child: _elkjs.ELKOutputChild
    ) -> aird.diagram._StyleOverrides | None:
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

            styleoverrides = style_condition(obj)
        return styleoverrides

    def check_boxlabel_space(self, box: aird.Box) -> None:
        """Check if size of parent boxes is enough for their label."""
        if not box.children or any(child.port for child in box.children):
            return

        child_dist = min(
            [
                abs(child.pos.y - box.pos.y)
                for child in box.children
                if isinstance(child, aird.Box)
            ]
        )

        label = box.label
        if isinstance(label, aird.Box):
            label = label.label
        elif label is None:
            return

        assert isinstance(label, str)
        lines = helpers.word_wrap(
            label, box.size.x - (2 * icon_padding + icon_size)
        )
        _, labelheight = helpers.extent_func(label)
        labelspace = aird.Vector2D(
            0,
            child_dist
            - (2 * collectors.makers.LABEL_VPAD + len(lines) * labelheight),
        )
        if labelspace.y >= 0:
            return

        box.pos += labelspace
        box.size += abs(labelspace)
        assert self.aird_diagram.viewport is not None
        viewport_dist = aird.Vector2D(
            0, box.pos.y + labelspace.y - self.aird_diagram.viewport.pos.y
        )
        if viewport_dist.y <= 0:
            self.aird_diagram.viewport.pos += viewport_dist
            self.aird_diagram.viewport.size += abs(viewport_dist)

    def check_edgelabel_space(self, edge: aird.Edge) -> None:
        """Check if any label is outside of the viewport."""
        if not edge.labels:
            return

        assert self.aird_diagram.viewport is not None
        lower_bound = (
            self.aird_diagram.viewport.pos + self.aird_diagram.viewport.size
        )
        for label in edge.labels:
            self._fix_lower_space(lower_bound, label)

    def check_viewBox_space(self, box: aird.Box) -> None:
        """Check if given box and its label fits inside the diagram."""
        assert self.aird_diagram.viewport is not None
        upper_bound = self.aird_diagram.viewport.pos
        lower_bound = upper_bound + self.aird_diagram.viewport.size
        self._fix_lower_space(lower_bound, box)
        self._fix_upper_space(upper_bound, box)
        if isinstance(box.label, aird.Box):
            self._fix_lower_space(lower_bound, box.label)
            self._fix_upper_space(upper_bound, box.label)

    def _fix_lower_space(
        self, lower_bound: aird.Vector2D, box: aird.Box
    ) -> None:
        assert self.aird_diagram.viewport is not None
        space = lower_bound - (box.pos + box.size)
        self.aird_diagram.viewport.size += aird.Vector2D(
            abs(space.x) if space.x <= 0 else 0,
            abs(space.y) if space.y <= 0 else 0,
        )

    def _fix_upper_space(
        self, upper_bound: aird.Vector2D, box: aird.Box
    ) -> None:
        assert self.aird_diagram.viewport is not None
        space = box.pos - upper_bound
        self.aird_diagram.viewport.pos -= aird.Vector2D(
            abs(space.x) if space.x <= 0 else 0,
            abs(space.y) if space.y <= 0 else 0,
        )


def get_styleclass(obj: common.GenericElement) -> str:
    """Return the styleclass for a given `obj`."""
    styleclass = obj.__class__.__name__
    styleclass = (
        aird.parser._semantic.STYLECLASS_LOOKUP.get(
            styleclass, (styleclass, None)
        )[0]
        or styleclass
    )
    if styleclass.endswith("Component"):
        styleclass = "".join(
            (
                styleclass[: -len("Component")],
                "Human" * obj.is_human,
                ("Component", "Actor")[obj.is_actor],
            )
        )
    elif styleclass == "CP":
        try:
            styleclass += f'_{obj._element.attrib["orientation"]}'
        except KeyError:
            styleclass = "CP_UNSET"
    return styleclass
