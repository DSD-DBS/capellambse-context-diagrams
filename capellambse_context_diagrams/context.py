# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""
Definitions of Custom Accessor- and Diagram-Classtypes based on
[`Accessor`][capellambse.model.common.accessors.Accessor] and [`AbstractDiagram`][capellambse.model.diagram.AbstractDiagram].
"""
from __future__ import annotations

import collections.abc as cabc
import copy
import json
import logging
import typing as t

from capellambse import diagram as cdiagram
from capellambse import helpers
from capellambse.model import common, diagram, modeltypes

from . import _elkjs, filters, serializers, styling
from .collectors import (
    dataflow_view,
    exchanges,
    get_elkdata,
    realization_view,
    tree_view,
)

logger = logging.getLogger(__name__)

STANDARD_FILTERS = {
    "Operational Capabilities Blank": filters.SYSTEM_EX_RELABEL,
    "Missions Capabilities Blank": filters.SYSTEM_EX_RELABEL,
}
STANDARD_STYLES = {
    "Operational Capabilities Blank": styling.SYSTEM_CAP_STYLING,
    "Missions Capabilities Blank": styling.SYSTEM_CAP_STYLING,
}


class ContextAccessor(common.Accessor):
    """Provides access to the context diagrams."""

    def __init__(
        self, dgcls: str, render_params: dict[str, t.Any] | None = None
    ) -> None:
        super().__init__()
        self._dgcls = dgcls
        self._default_render_params = render_params or {}

    @t.overload
    def __get__(self, obj: None, objtype: type[t.Any]) -> ContextAccessor: ...

    @t.overload
    def __get__(
        self,
        obj: common.T,
        objtype: type[common.T] | None = None,
    ) -> ContextDiagram: ...

    def __get__(
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(obj, ContextDiagram)

    def _get(
        self,
        obj: common.GenericElement,
        diagram_class: type[ContextDiagram],
        diagram_id: str = "{}_context",
    ) -> common.Accessor | ContextDiagram:
        try:
            cache = getattr(
                obj._model, ".".join((__name__, diagram_class.__qualname__))
            )
        except AttributeError:
            cache = {}
            setattr(
                obj._model,
                ".".join((__name__, diagram_class.__qualname__)),
                cache,
            )
        diagram_id = diagram_id.format(obj.uuid)
        try:
            return cache[diagram_id]
        except KeyError:
            pass

        new_diagram = diagram_class(
            self._dgcls, obj, **self._default_render_params
        )
        new_diagram.filters.add(filters.NO_UUID)
        cache[diagram_id] = new_diagram
        return new_diagram


class InterfaceContextAccessor(ContextAccessor):
    """Provides access to the interface context diagrams."""

    def __init__(  # pylint: disable=super-init-not-called
        self,
        diagclass: dict[type[common.GenericElement], str],
        render_params: dict[str, t.Any] | None = None,
    ) -> None:
        self.__dgclasses = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        assert isinstance(obj.parent, common.GenericElement)
        self._dgcls = self.__dgclasses[obj.parent.__class__]
        return self._get(obj, InterfaceContextDiagram, "{}_interface_context")


class FunctionalContextAccessor(ContextAccessor):
    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(
            obj, FunctionalContextDiagram, "{}_functional_context"
        )


class ClassTreeAccessor(ContextAccessor):
    """Provides access to the tree view diagrams."""

    # pylint: disable=super-init-not-called
    def __init__(
        self, diagclass: str, render_params: dict[str, t.Any] | None = None
    ) -> None:
        self._dgcls = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ClassTreeDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(obj, ClassTreeDiagram, "{}_class_tree")


class RealizationViewContextAccessor(ContextAccessor):
    """Provides access to the realization view diagrams."""

    # pylint: disable=super-init-not-called
    def __init__(
        self, diagclass: str, render_params: dict[str, t.Any] | None = None
    ) -> None:
        self._dgcls = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a RealizationViewDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(obj, RealizationViewDiagram, "{}_realization_view")


class DataFlowAccessor(ContextAccessor):
    # pylint: disable=super-init-not-called
    def __init__(
        self, diagclass: str, render_params: dict[str, t.Any] | None = None
    ) -> None:
        self._dgcls = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a DataFlowViewDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(obj, DataFlowViewDiagram, "{}_data_flow_view")


class ContextDiagram(diagram.AbstractDiagram):
    """An automatically generated context diagram.

    Attributes
    ----------
    target
        The `common.GenericElement` from which the context is collected
        from.
    styleclass
        The diagram class (for e.g. [LAB]).
    render_styles
        Dictionary with the `ElkChildType` in str format as keys and
        `styling.Styler` functions as values. An example is given by:
        [`styling.BLUE_ACTOR_FNCS`][capellambse_context_diagrams.styling.BLUE_ACTOR_FNCS]
    display_symbols_as_boxes
        Display objects that are normally displayed as symbol as a
        simple box instead, with the symbol being the box' icon. This
        avoids the object of interest to become one giant, oversized
        symbol in the middle of the diagram, and instead keeps the
        symbol small and only enlarges the surrounding box.
    display_parent_relation
        Display objects with a parent relationship to the object of
        interest as the parent box.
    display_derived_interfaces
        Display derived objects collected from additional collectors
        beside the main collector for building the context.
    slim_center_box
        Minimal width for the center box, containing just the icon and
        the label. This is False if hierarchy was identified.
    serializer
        The serializer builds a `diagram.Diagram` via
        [`serializers.DiagramSerializer.make_diagram`][capellambse_context_diagrams.serializers.DiagramSerializer.make_diagram]
        by converting every
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild]
        into a `diagram.Box`, `diagram.Edge` or `diagram.Circle`.
    filters
        A list of filter names that are applied during collection of
        context. Currently this is only done in
        [`collectors.exchange_data_collector`][capellambse_context_diagrams.collectors.generic.exchange_data_collector].
    """

    def __init__(
        self,
        class_: str,
        obj: common.GenericElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        display_symbols_as_boxes: bool = False,
        display_parent_relation: bool = False,
        display_derived_interfaces: bool = False,
        slim_center_box: bool = True,
    ) -> None:
        super().__init__(obj._model)
        self.target = obj
        self.styleclass = class_

        self.render_styles = render_styles or {}
        self.serializer = serializers.DiagramSerializer(self)
        self.__filters: cabc.MutableSet[str] = self.FilterSet(self)
        self.display_symbols_as_boxes = display_symbols_as_boxes
        self.display_parent_relation = display_parent_relation
        self.display_derived_interfaces = display_derived_interfaces
        self.slim_center_box = slim_center_box

        if standard_filter := STANDARD_FILTERS.get(class_):
            self.filters.add(standard_filter)
        if standard_styles := STANDARD_STYLES.get(class_):
            self.render_styles = standard_styles

    @property
    def uuid(self) -> str:  # type: ignore
        """Returns diagram UUID."""
        return f"{self.target.uuid}_context"

    @property
    def name(self) -> str:  # type: ignore
        """Returns the diagram name."""
        return f"Context of {self.target.name.replace('/', '- or -')}"

    @property
    def type(self) -> modeltypes.DiagramType:
        """Return the type of this diagram."""
        try:
            return modeltypes.DiagramType(self.styleclass)
        except ValueError:  # pragma: no cover
            logger.warning("Unknown diagram type %r", self.styleclass)
            return modeltypes.DiagramType.UNKNOWN

    class FilterSet(cabc.MutableSet):
        """A set that stores filter_names and invalidates diagram cache."""

        def __init__(
            self,
            diagram: diagram.AbstractDiagram,  # pylint: disable=redefined-outer-name
        ) -> None:
            self._set: set[str] = set()
            self._diagram = diagram

        def add(self, value: str) -> None:
            if value not in filters.FILTER_LABEL_ADJUSTERS:
                logger.error("The filter '%s' is not yet supported.", value)
                return
            if value not in self._set:
                self._set.add(value)
                self._diagram.invalidate_cache()

        def discard(self, value: str) -> None:
            if value in self._set:
                self._diagram.invalidate_cache()
            return self._set.discard(value)

        def __contains__(self, x: object) -> bool:
            return self._set.__contains__(x)

        def __iter__(self) -> cabc.Iterator[str]:
            return self._set.__iter__()

        def __len__(self) -> int:
            return self._set.__len__()

    def render(self, fmt: str | None, /, **params) -> t.Any:
        """Render the diagram in the given format."""
        rparams = params.copy()
        for attr, value in params.items():
            attribute = getattr(self, attr, "NOT_FOUND")
            if attribute not in {"NOT_FOUND", value}:
                self.invalidate_cache()

                setattr(self, attr, value)
                del rparams[attr]
        return super().render(fmt, **rparams)

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        transparent_background = params.pop("transparent_background", False)
        self.display_parent_relation = params.pop(
            "display_parent_relation", self.display_parent_relation
        )
        self.display_derived_interfaces = params.pop(
            "display_derived_interfaces", self.display_derived_interfaces
        )
        self.display_symbols_as_boxes = params.pop(
            "display_symbols_as_boxes", self.display_symbols_as_boxes
        )
        self.slim_center_box = params.pop(
            "slim_center_box", self.slim_center_box
        )
        data = params.get("elkdata") or get_elkdata(self, params)
        layout = try_to_layout(data)
        add_context(layout, params.get("is_legend", False))
        return self.serializer.make_diagram(
            layout,
            transparent_background=transparent_background,
        )

    @property  # type: ignore
    def filters(self) -> cabc.MutableSet[str]:  # type: ignore
        return self.__filters

    @filters.setter
    def filters(self, value: cabc.Iterable[str]) -> None:
        self.__filters.clear()
        self.__filters |= set(value)


class InterfaceContextDiagram(ContextDiagram):
    """An automatically generated Context Diagram exclusively for
    ``ComponentExchange``s.
    """

    def __init__(
        self,
        class_: str,
        obj: common.GenericElement,
        include_interface: bool = False,
        **kw,
    ) -> None:
        self.include_interface = include_interface
        super().__init__(class_, obj, **kw, display_symbols_as_boxes=True)

    @property
    def name(self) -> str:  # type: ignore
        return f"Interface Context of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        params["elkdata"] = exchanges.get_elkdata_for_exchanges(
            self, exchanges.InterfaceContextCollector, params
        )
        return super()._create_diagram(params)


class FunctionalContextDiagram(ContextDiagram):
    """An automatically generated Context Diagram exclusively for
    Components.
    """

    @property
    def name(self) -> str:  # type: ignore
        return f"Interface Context of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        params["elkdata"] = exchanges.get_elkdata_for_exchanges(
            self, exchanges.FunctionalContextCollector, params
        )
        return super()._create_diagram(params)


class ClassTreeDiagram(ContextDiagram):
    """An automatically generated ClassTree Diagram.

    This diagram is exclusively for ``Class``es.
    """

    def __init__(self, class_: str, obj: common.GenericElement, **kw) -> None:
        super().__init__(class_, obj, **kw, display_symbols_as_boxes=True)

    @property
    def uuid(self) -> str:  # type: ignore
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_tree_view"

    @property
    def name(self) -> str:  # type: ignore
        """Returns the name of the diagram."""
        return f"Tree view of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        params.setdefault("algorithm", params.get("algorithm", "layered"))
        params.setdefault("elk.direction", params.pop("direction", "DOWN"))
        params.setdefault("edgeRouting", params.get("edgeRouting", "POLYLINE"))
        params.setdefault(
            "nodeSize.constraints",
            params.pop("nodeSizeConstraints", "NODE_LABELS"),
        )
        params.setdefault(
            "partitioning.activate", params.pop("partitioning", False)
        )
        params.setdefault(
            "layered.edgeLabels.sideSelection",
            params.pop("edgeLabelsSide", "SMART_DOWN"),
        )
        data, legend = tree_view.collector(self, params)
        params["elkdata"] = data
        class_diagram = super()._create_diagram(params)
        width, height = class_diagram.viewport.size
        axis: t.Literal["x", "y"]
        if params["elk.direction"] in {"DOWN", "UP"}:
            legend["layoutOptions"]["aspectRatio"] = width / height
            axis = "x"
        else:
            legend["layoutOptions"]["aspectRatio"] = width
            axis = "y"
        params["elkdata"] = legend
        params["is_legend"] = True
        legend_diagram = super()._create_diagram(params)
        stack_diagrams(class_diagram, legend_diagram, axis)
        return class_diagram


def add_context(data: _elkjs.ELKOutputData, is_legend: bool = False) -> None:
    """Add all connected nodes as context to all elements."""
    if is_legend:
        for child in data["children"]:
            if child["type"] == "node":
                child["context"] = [child["id"]]  # type: ignore[typeddict-unknown-key]
        return

    ids: set[str] = set()

    def get_ids(
        obj: (
            _elkjs.ELKOutputNode
            | _elkjs.ELKOutputPort
            | _elkjs.ELKOutputJunction
            | _elkjs.ELKOutputEdge
        ),
    ) -> None:
        if obj["id"] and not obj["id"].startswith("g_"):
            ids.add(obj["id"])
        for child in obj.get("children", []):
            if child["type"] in {"node", "port", "junction", "edge"}:
                assert child["type"] != "label"
                get_ids(child)

    def set_ids(
        obj: _elkjs.ELKOutputChild,
        ids: set[str],
    ) -> None:
        obj["context"] = list(ids)  # type: ignore[typeddict-unknown-key]
        for child in obj.get("children", []):  # type: ignore[attr-defined]
            set_ids(child, ids)

    for child in data["children"]:
        if child["type"] in {"node", "port", "junction", "edge"}:
            assert child["type"] != "label"
            get_ids(child)

    for child in data["children"]:
        set_ids(child, ids)


class RealizationViewDiagram(ContextDiagram):
    """An automatically generated RealizationViewDiagram Diagram.

    This diagram is exclusively for ``Activity``, ``Function``s,
    ``Entity`` and ``Components`` of all layers.
    """

    def __init__(self, class_: str, obj: common.GenericElement, **kw) -> None:
        super().__init__(class_, obj, **kw, display_symbols_as_boxes=True)

    @property
    def uuid(self) -> str:  # type: ignore
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_realization_view"

    @property
    def name(self) -> str:  # type: ignore
        """Returns the name of the diagram."""
        return f"Realization view of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        params.setdefault("depth", params.get("depth", 1))
        params.setdefault(
            "search_direction", params.get("search_direction", "ALL")
        )
        params.setdefault("show_owners", True)
        params.setdefault("layer_sizing", "WIDTH")
        data, edges = realization_view.collector(self, params)
        layout = try_to_layout(data)
        adjust_layer_sizing(data, layout, params["layer_sizing"])
        layout = try_to_layout(data)
        for edge in edges:
            layout["children"].append(
                {
                    "id": edge["id"],
                    "type": "edge",
                    "sourceId": edge["sources"][0],
                    "targetId": edge["targets"][0],
                    "routingPoints": [],
                    "styleclass": "Realization",
                }  # type: ignore[arg-type]
            )
        self._add_layer_labels(layout)
        return self.serializer.make_diagram(
            layout,
            transparent_background=params.get("transparent_background", False),
        )

    def _add_layer_labels(self, layout: _elkjs.ELKOutputData) -> None:
        for layer in layout["children"]:
            if layer["type"] != "node":
                continue

            layer_obj = self.serializer.model.by_uuid(layer["id"])
            _, layer_name = realization_view.find_layer(layer_obj)
            pos = layer["position"]["x"], layer["position"]["y"]
            size = layer["size"]["width"], layer["size"]["height"]
            width, height = helpers.get_text_extent(layer_name)
            x, y, tspan_y = calculate_label_position(*pos, *size)
            label_box: _elkjs.ELKOutputChild = {
                "type": "label",
                "id": "None",
                "text": layer_name,
                "position": {"x": x, "y": y},
                "size": {"width": width, "height": height},
                "style": {
                    "text_transform": f"rotate(-90, {x}, {y}) {tspan_y}",
                    "text_fill": "grey",
                },
            }
            layer["children"].insert(0, label_box)
            layer["style"] = {"stroke": "grey", "rx": 5, "ry": 5}


class DataFlowViewDiagram(ContextDiagram):
    """An automatically generated DataFlowViewDiagram."""

    def __init__(self, class_: str, obj: common.GenericElement, **kw) -> None:
        super().__init__(class_, obj, **kw, display_symbols_as_boxes=True)

    @property
    def uuid(self) -> str:  # type: ignore
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_data_flow_view"

    @property
    def name(self) -> str:  # type: ignore
        """Returns the name of the diagram."""
        return f"DataFlow view of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        params["elkdata"] = dataflow_view.collector(self, params)
        return super()._create_diagram(params)


def try_to_layout(data: _elkjs.ELKInputData) -> _elkjs.ELKOutputData:
    """Try calling elkjs, raise a JSONDecodeError if it fails."""
    try:
        return _elkjs.call_elkjs(data)
    except json.JSONDecodeError as error:
        logger.error(json.dumps(data, indent=4))
        raise error


def adjust_layer_sizing(
    data: _elkjs.ELKInputData,
    layout: _elkjs.ELKOutputData,
    layer_sizing: t.Literal["UNION", "WIDTH", "HEIGHT"],
) -> None:
    """Set `nodeSize.minimum` config in the layoutOptions."""

    def calculate_min(key: t.Literal["width", "height"] = "width") -> float:
        return max(child["size"][key] for child in layout["children"])  # type: ignore[typeddict-item]

    if layer_sizing not in {"UNION", "WIDTH", "HEIGHT", "INDIVIDUAL"}:
        raise NotImplementedError(
            "For ``layer_sizing`` only UNION, WIDTH, HEIGHT or INDIVIDUAL is supported"
        )

    min_w = calculate_min() + 15.0 if layer_sizing in {"UNION", "WIDTH"} else 0
    min_h = (
        calculate_min("height") if layer_sizing in {"UNION", "HEIGHT"} else 0
    )
    for layer in data["children"]:
        layer["layoutOptions"]["nodeSize.minimum"] = f"({min_w},{min_h})"


def stack_diagrams(
    first: cdiagram.Diagram,
    second: cdiagram.Diagram,
    axis: t.Literal["x", "y"] = "x",
) -> None:
    """Add the diagram elements from ``right`` to left inline."""
    if first.viewport:
        offset = first.viewport.pos + first.viewport.size
        offset @= (1, 0) if axis == "x" else (0, 1)
        for element in second:
            new = copy.deepcopy(element)
            new.move(offset)
            first += new
    else:
        for element in second:
            new = copy.deepcopy(element)
            first += new


def calculate_label_position(
    x: float,
    y: float,
    width: float,
    height: float,
    padding: float = 10,
) -> tuple[float, float, float]:
    """Calculate the position of the label and tspan.

    The function calculates the center of the rectangle and uses the
    rectangle's width and height to adjust its position within it. The
    text is assumed to be horizontally and vertically centered within
    the rectangle. The tspan y coordinate is for positioning the label
    right under the left side of the rectangle.

    Parameters
    ----------

    Returns
    -------
    tuple
        A tuple containing the x- and y-coordinate for the text element
        and the adjusted y-coordinate for the tspan element.
    """
    center_y = y + height / 2
    tspan_y = center_y - width / 2 + padding
    return (x + width / 2, center_y, tspan_y)
