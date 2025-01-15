# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Extends the capellambse.model.diagram module with context diagrams.

Definitions of Custom Accessor- and Diagram-Classtypes based on
[`Accessor`][capellambse.model.Accessor] and
[`AbstractDiagram`][capellambse.model.diagram.AbstractDiagram].
"""

from __future__ import annotations

import collections.abc as cabc
import copy
import json
import logging
import typing as t

from capellambse import diagram as cdiagram
from capellambse import helpers
from capellambse import model as m

from . import _elkjs, filters, serializers, styling
from .collectors import (
    cable_tree,
    custom,
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

CollectorOutputData: t.TypeAlias = (
    _elkjs.ELKInputData
    | tuple[
        _elkjs.ELKInputData, _elkjs.ELKInputData | list[_elkjs.ELKInputEdge]
    ]
)
"""The output of a collector or the input prepared for ELK."""


class ContextAccessor(m.Accessor):
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
        self, obj: m.T, objtype: type[m.T] | None = None
    ) -> ContextDiagram: ...
    def __get__(
        self, obj: m.T | None, objtype: type | None = None
    ) -> m.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, ContextDiagram)

    def _get(
        self, obj: m.ModelElement, diagram_class: type[ContextDiagram]
    ) -> m.Accessor | ContextDiagram:
        new_diagram = diagram_class(
            self._dgcls,
            obj,
            default_render_parameters=self._default_render_params,
        )
        new_diagram.filters.add(filters.NO_UUID)
        return new_diagram


class InterfaceContextAccessor(ContextAccessor):
    """Provides access to the interface context diagrams."""

    def __init__(  # pylint: disable=super-init-not-called
        self,
        diagclass: dict[type[m.ModelElement], str],
        render_params: dict[str, t.Any] | None = None,
    ) -> None:
        self.__dgclasses = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self, obj: m.T | None, objtype: type | None = None
    ) -> m.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        assert isinstance(obj.parent, m.ModelElement)
        self._dgcls = self.__dgclasses[obj.parent.__class__]
        return self._get(obj, InterfaceContextDiagram)


class FunctionalContextAccessor(ContextAccessor):
    def __get__(  # type: ignore
        self,
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, FunctionalContextDiagram)


class PhysicalPortContextAccessor(ContextAccessor):
    def __get__(  # type: ignore
        self,
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, PhysicalPortContextDiagram)


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
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a ClassTreeDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, ClassTreeDiagram)


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
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a RealizationViewDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, RealizationViewDiagram)


class DataFlowAccessor(ContextAccessor):
    # pylint: disable=super-init-not-called
    def __init__(
        self, diagclass: str, render_params: dict[str, t.Any] | None = None
    ) -> None:
        self._dgcls = diagclass
        self._default_render_params = render_params or {}

    def __get__(  # type: ignore
        self,
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a DataFlowViewDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, DataFlowViewDiagram)


class CableTreeAccessor(ContextAccessor):
    """Provides access to the cable tree diagrams."""

    def __get__(  # type: ignore
        self,
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a CableTreeView for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, CableTreeViewDiagram)


class CustomContextAccessor(ContextAccessor):
    """Provides access to the custom context diagrams."""

    def __get__(  # type: ignore
        self,
        obj: m.T | None,
        objtype: type | None = None,
    ) -> m.Accessor | ContextDiagram:
        """Make a CustomDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, m.ModelElement)
        return self._get(obj, CustomDiagram)


class ContextDiagram(m.AbstractDiagram):
    """An automatically generated context diagram.

    Attributes
    ----------
    target
        The `m.ModelElement` from which the context is collected
        from.
    styleclass
        The diagram class (for e.g. [LAB]).
    render_styles
        Dictionary with the `ElkChildType` in str format as keys and
        `styling.Styler` functions as values. An example is given by:
        [`styling.BLUE_ACTOR_FNCS`][capellambse_context_diagrams.styling.BLUE_ACTOR_FNCS]
    serializer
        The serializer builds a `Diagram` via
        [`serializers.DiagramSerializer.make_diagram`][capellambse_context_diagrams.serializers.DiagramSerializer.make_diagram]
        by converting every
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild]
        into a `Box`, `Edge` or `Circle`.
    filters
        A list of filter names that are applied during collection of
        context. Currently this is only done in
        [`collectors.exchange_data_collector`][capellambse_context_diagrams.collectors.generic.exchange_data_collector].

    Notes
    -----
    * display_symbols_as_boxes — Display objects that are normally
      displayed as symbol as a simple box instead, with the symbol
      being the box' icon. This avoids the object of interest to
      become one giant, oversized symbol in the middle of the diagram,
      and instead keeps the symbol small and only enlarges the
      surrounding box.
    * display_parent_relation — Display objects with a parent
      relationship to the object of interest as the parent box.
    * display_derived_interfaces — Display derived objects collected
      from additional collectors beside the main collector for building
      the context.
    * slim_center_box — Minimal width for the center box, containing
      just the icon and the label. This is False if hierarchy was
      identified.
    * display_port_labels — Display port labels on the diagram.
    * port_label_position - Position of the port labels. See
      [`PORT_LABEL_POSITION`][capellambse_context_diagrams.context._elkjs.PORT_LABEL_POSITION].
    * hide_direct_children - Hide direct children of the object of
      interest.
    * display_unused_ports - Display ports that are not connected to an edge.
    """

    _display_symbols_as_boxes: bool
    _display_parent_relation: bool
    _hide_direct_children: bool
    _display_derived_interfaces: bool
    _slim_center_box: bool
    _display_port_labels: bool
    _port_label_position: str
    _transparent_background: bool
    _display_unused_ports: bool

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        super().__init__(obj._model)
        self.target = obj  # type: ignore[misc]
        self.styleclass = class_

        self.render_styles = render_styles or {}
        self.serializer = serializers.DiagramSerializer(self)

        self._elk_input_data: CollectorOutputData | None = None
        self.__filters: cabc.MutableSet[str] = self.FilterSet(self)
        self._default_render_parameters = {
            "display_symbols_as_boxes": False,
            "display_parent_relation": False,
            "hide_direct_children": False,
            "display_derived_interfaces": False,
            "slim_center_box": True,
            "display_port_labels": False,
            "port_label_position": _elkjs.PORT_LABEL_POSITION.OUTSIDE.name,
            "display_unused_ports": False,
            "transparent_background": False,
        } | default_render_parameters

        if standard_filter := STANDARD_FILTERS.get(class_):
            self.filters.add(standard_filter)
        if standard_styles := STANDARD_STYLES.get(class_):
            self.render_styles = standard_styles

        self.collector: cabc.Callable[
            [ContextDiagram, dict[str, t.Any]], CollectorOutputData
        ] = get_elkdata

    @property
    def uuid(self) -> str:
        """Returns diagram UUID."""
        return f"{self.target.uuid}_context"

    @property
    def name(self) -> str:
        """Returns the diagram name."""
        return f"Context of {self.target.name.replace('/', '- or -')}"

    @property
    def type(self) -> m.DiagramType:
        """Return the type of this diagram."""
        try:
            return m.DiagramType(self.styleclass)
        except ValueError:  # pragma: no cover
            logger.warning("Unknown diagram type %r", self.styleclass)
            return m.DiagramType.UNKNOWN

    @property
    def nodes(self) -> m.MixedElementList:
        """Return a list of all nodes visible in this diagram."""
        allids = {e.uuid for e in self.render(None) if not e.hidden}
        elems = []
        for elemid in allids:
            assert elemid is not None
            try:
                elem = self._model.by_uuid(elemid)
            except (KeyError, ValueError):
                continue

            elems.append(elem._element)
        return m.MixedElementList(self._model, elems, m.ModelElement)

    def elk_input_data(self, params: dict[str, t.Any]) -> CollectorOutputData:
        """Return the collected ELK input data."""
        params = self._default_render_parameters | params
        for param_name in self._default_render_parameters:
            setattr(self, f"_{param_name}", params.pop(param_name))

        data: CollectorOutputData
        if data := params.get("elkdata", None):  # type: ignore[assignment]
            self._elk_input_data = data

        if self._elk_input_data is None:
            self._elk_input_data = self.collector(self, params)

        return self._elk_input_data

    def invalidate_cache(self) -> None:
        super().invalidate_cache()
        self._elk_input_data = None

    class FilterSet(cabc.MutableSet):
        """A set that stores filter_names and invalidates diagram cache."""

        def __init__(
            self,
            diagram: m.AbstractDiagram,
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

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        data = self.elk_input_data(params)
        assert not isinstance(data, tuple)
        layout = try_to_layout(data)
        is_legend: bool = params.get("is_legend", False)
        add_context(layout, is_legend)
        return self.serializer.make_diagram(
            layout, transparent_background=self._transparent_background
        )

    @property
    def filters(self) -> cabc.MutableSet[str]:
        return self.__filters

    @filters.setter
    def filters(self, value: cabc.Iterable[str]) -> None:
        self.__filters.clear()
        self.__filters |= set(value)


class InterfaceContextDiagram(ContextDiagram):
    """A Context Diagram exclusively for ``ComponentExchange``s.

    Attributes
    ----------
    dangling_functional_exchanges: list[fa.AbstractExchange]
        A list of ``dangling`` functional exchanges for which either the
        source or target function were not allocated to a Component,
        part of the context.

    Notes
    -----
    The following render parameters are available:

    * include_interface — Boolean flag to enable inclusion of the
      context diagram target: The interface ComponentExchange.
    * include_port_allocations — Boolean flag to enable rendering of
      port allocations.
    * hide_functions — Boolean flag to enable white box view: Only
      displaying Components or Entities.
    * display_port_labels — Display port labels on the diagram.
    * port_label_position — Position of the port labels. See
      [`PORT_LABEL_POSITION`][capellambse_context_diagrams.context._elkjs.PORT_LABEL_POSITION].

    In addition to all other render parameters of
    [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram].
    """

    _include_interface: bool
    _include_port_allocations: bool
    _hide_functions: bool
    _display_port_labels: bool
    _port_label_position: str

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "include_interface": False,
            "include_port_allocations": False,
            "hide_functions": False,
            "display_symbols_as_boxes": True,
            "display_port_labels": False,
            "port_label_position": _elkjs.PORT_LABEL_POSITION.OUTSIDE.name,
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector: cabc.Callable[
            [InterfaceContextDiagram, dict[str, t.Any]], _elkjs.ELKInputData
        ] = exchanges.interface_context_collector

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        data = self.elk_input_data(params)
        assert not isinstance(data, tuple)
        layout = try_to_layout(data)
        if self._include_interface and self._include_port_allocations:
            self._add_port_allocations(layout)

        is_legend: bool = params.get("is_legend", False)
        add_context(layout, is_legend)
        return self.serializer.make_diagram(
            layout, transparent_background=self._transparent_background
        )

    def _add_port_allocations(self, layout: _elkjs.ELKOutputData) -> None:
        for i, uuid in enumerate(
            (self.target.source.uuid, self.target.target.uuid)
        ):
            node = layout.children[i]
            assert isinstance(node, _elkjs.ELKOutputNode)
            port = next((p for p in node.children if p.id == uuid), None)
            assert isinstance(port, _elkjs.ELKOutputPort)
            if port is not None:
                layout.children.extend(
                    self._yield_port_allocations(node, port)
                )

    def _yield_port_allocations(
        self, node: _elkjs.ELKOutputNode, interface_port: _elkjs.ELKOutputPort
    ) -> cabc.Iterator[_elkjs.ELKOutputEdge]:
        ref = cdiagram.Vector2D(node.position.x, node.position.y)
        for position, port in _get_all_ports(node, ref=ref):
            if port == interface_port:
                continue

            port_middle = _calculate_middle(position, port.size)
            interface_middle = _calculate_middle(
                interface_port.position, interface_port.size, node.position
            )
            styleclass = self.serializer.get_styleclass(port.id)
            if styleclass in {"FIP", "FOP"}:
                yield _create_edge(
                    styleclass,
                    port.id,
                    interface_port.id,
                    port_middle,
                    interface_middle,
                )

    @property
    def name(self) -> str:
        return f"Interface Context of {self.target.name}"


def _create_edge(
    styleclass, port_id, interface_id, port_middle, interface_middle
) -> _elkjs.ELKOutputEdge:
    if styleclass == "FIP":
        eid = f"__PortInputAllocation:{port_id}"
        src_id, trg_id = port_id, interface_id
        routing_points = [port_middle, interface_middle]
    else:
        eid = f"__PortOutputAllocation:{port_id}"
        src_id, trg_id = interface_id, port_id
        routing_points = [interface_middle, port_middle]

    return _elkjs.ELKOutputEdge(
        id=eid,
        type="edge",
        routingPoints=routing_points,
        sourceId=src_id,
        targetId=trg_id,
    )


class FunctionalContextDiagram(ContextDiagram):
    """A Context Diagram exclusively for Components."""

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        default_render_parameters: dict[str, t.Any],
    ):
        super().__init__(
            class_, obj, default_render_parameters=default_render_parameters
        )

        self.collector: cabc.Callable[
            [FunctionalContextDiagram, dict[str, t.Any]], _elkjs.ELKInputData
        ] = exchanges.functional_context_collector

    @property
    def name(self) -> str:
        return f"Interface Context of {self.target.name}"


class ClassTreeDiagram(ContextDiagram):
    """An automatically generated ClassTree Diagram.

    This diagram is exclusively for ``Class``es.
    """

    _display_symbols_as_boxes: bool
    _edgeRouting: t.Literal["UNDEFINED", "POLYLINE", "ORTHOGONAL", "SPLINES"]
    _direction: t.Literal["DOWN", "UP", "LEFT", "RIGHT"]
    _nodeSizeConstraints: t.Literal[
        "PORTS", "PORT_LABELS", "NODE_LABELS", "MINIMUM_SIZE"
    ]
    _edgeLabelsSide: t.Literal[
        "ALWAYS_UP",
        "ALWAYS_DOWN",
        "DIRECTION_UP",
        "DIRECTION_DOWN",
        "SMART_UP",
        "SMART_DOWN",
    ]
    _partitioning: bool

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "display_symbols_as_boxes": True,
            "edgeRouting": "POLYLINE",
            "direction": "DOWN",
            "nodeSizeConstraints": "NODE_LABELS",
            "edgeLabelsSide": "SMART_DOWN",
            "partitioning": False,
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector = tree_view.collector

    @property
    def uuid(self) -> str:
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_tree_view"

    @property
    def name(self) -> str:
        """Returns the name of the diagram."""
        return f"Tree view of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        data, legend = self.elk_input_data(params)
        assert isinstance(data, _elkjs.ELKInputData)
        assert isinstance(legend, _elkjs.ELKInputData)
        params["elkdata"] = data
        class_diagram = super()._create_diagram(params)
        assert class_diagram.viewport is not None
        width, height = class_diagram.viewport.size
        axis: t.Literal["x", "y"]
        if self._direction in {"DOWN", "UP"}:
            legend.layoutOptions["aspectRatio"] = width / height
            axis = "x"
        else:
            legend.layoutOptions["aspectRatio"] = width
            axis = "y"

        params["elkdata"] = legend
        params["is_legend"] = True
        legend_diagram = super()._create_diagram(params)
        stack_diagrams(class_diagram, legend_diagram, axis)
        return class_diagram


def add_context(data: _elkjs.ELKOutputData, is_legend: bool = False) -> None:
    """Add all connected nodes as context to all elements."""
    if is_legend:
        for child in data.children:
            if child.type == "node":
                child.context = [child.id]
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
        if obj.id and not obj.id.startswith("g_"):
            ids.add(obj.id)
        for child in getattr(obj, "children", []):
            if child.type in {"node", "port", "junction", "edge"}:
                assert child.type != "label"
                get_ids(child)

    def set_ids(
        obj: _elkjs.ELKOutputChild,
        ids: set[str],
    ) -> None:
        obj.context = list(ids)
        for child in getattr(obj, "children", []):
            set_ids(child, ids)

    for child in data.children:
        if child.type in {"node", "port", "junction", "edge"}:
            assert child.type != "label"
            get_ids(child)

    for child in data.children:
        set_ids(child, ids)


class RealizationViewDiagram(ContextDiagram):
    """An automatically generated RealizationViewDiagram Diagram.

    This diagram is exclusively for ``Activity``, ``Function``s,
    ``Entity`` and ``Components`` of all layers.
    """

    _display_symbols_as_boxes: bool
    _depth: int
    _search_direction: t.Literal["ALL", "ABOVE", "BELOW"]
    _show_owners: bool
    _layer_sizing: t.Literal["UNION", "HEIGHT", "WIDTH", "INDIVIDUAL"]

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "display_symbols_as_boxes": True,
            "depth": 1,
            "search_direction": "ALL",
            "show_owners": True,
            "layer_sizing": "WIDTH",
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector = realization_view.collector

    @property
    def uuid(self) -> str:
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_realization_view"

    @property
    def name(self) -> str:
        """Returns the name of the diagram."""
        return f"Realization view of {self.target.name}"

    def _create_diagram(self, params: dict[str, t.Any]) -> cdiagram.Diagram:
        data, edges = self.elk_input_data(params)
        assert isinstance(data, _elkjs.ELKInputData)
        assert isinstance(edges, list)
        layout = try_to_layout(data)
        adjust_layer_sizing(data, layout, self._layer_sizing)
        layout = try_to_layout(data)
        for edge in edges:
            assert isinstance(edge, _elkjs.ELKInputEdge)
            layout.children.append(
                _elkjs.ELKOutputEdge(
                    id=f"__Realization:{edge.id}",
                    type="edge",
                    sourceId=edge.sources[0],
                    targetId=edge.targets[0],
                    routingPoints=[],
                )
            )
        self._add_layer_labels(layout)
        return self.serializer.make_diagram(
            layout, transparent_background=self._transparent_background
        )

    def _add_layer_labels(self, layout: _elkjs.ELKOutputData) -> None:
        for layer in layout.children:
            if layer.type != "node":
                continue

            layer_obj = self.serializer.model.by_uuid(layer.id)
            _, layer_name = realization_view.find_layer(layer_obj)
            pos = layer.position.x, layer.position.y
            size = layer.size.width, layer.size.height
            width, height = helpers.get_text_extent(layer_name)
            x, y, tspan_y = calculate_label_position(*pos, *size)
            label_box = _elkjs.ELKOutputLabel(
                type="label",
                id="None",
                text=layer_name,
                position=_elkjs.ELKPoint(x=x, y=y),
                size=_elkjs.ELKSize(width=width, height=height),
                style={
                    "text_transform": f"rotate(-90, {x}, {y}) {tspan_y}",
                    "text_fill": "grey",
                },
            )
            layer.children.insert(0, label_box)
            layer.style = {"stroke": "grey", "rx": 5, "ry": 5}


class DataFlowViewDiagram(ContextDiagram):
    """An automatically generated DataFlowViewDiagram."""

    _display_symbols_as_boxes: bool

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "display_symbols_as_boxes": True,
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector = dataflow_view.collector

    @property
    def uuid(self) -> str:
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_data_flow_view"

    @property
    def name(self) -> str:
        """Returns the name of the diagram."""
        return f"DataFlow view of {self.target.name}"


class CableTreeViewDiagram(ContextDiagram):
    """An automatically generated CableTreeView."""

    _display_port_labels: bool
    _port_label_position: str

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "display_port_labels": True,
            "port_label_position": _elkjs.PORT_LABEL_POSITION.OUTSIDE.name,
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector = cable_tree.collector

    @property
    def uuid(self) -> str:
        """Returns the UUID of the diagram."""
        return f"{self.target.uuid}_cable_tree"

    @property
    def name(self) -> str:
        return f"Cable Tree View of {self.target.name}"


class CustomDiagram(ContextDiagram):
    """An automatically generated CustomDiagram Diagram."""

    _collect: cabc.Iterator[m.ModelElement]
    _unify_edge_direction: str

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        default_render_parameters = {
            "collect": [],
            "slim_center_box": False,
            "unify_edge_direction": str,
        } | default_render_parameters
        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )
        self.collector = custom.collector

    @property
    def name(self) -> str:
        return f"Custom Context of {self.target.name.replace('/', '- or -')}"


class PhysicalPortContextDiagram(CustomDiagram):
    """A custom Context Diagram exclusively for PhysicalPorts."""

    def __init__(
        self,
        class_: str,
        obj: m.ModelElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        default_render_parameters: dict[str, t.Any],
    ) -> None:
        visited = set()

        def _collector(
            target: m.ModelElement,
        ) -> cabc.Iterator[m.ModelElement]:
            if target.uuid in visited:
                return
            visited.add(target.uuid)
            for link in target.links:
                yield link
                yield from _collector(link.source)
                yield from _collector(link.target)

        default_render_parameters = {
            "collect": _collector(obj),
            "display_parent_relation": True,
            "unify_edge_direction": "UNIFORM",
            "display_port_labels": True,
            "port_label_position": _elkjs.PORT_LABEL_POSITION.OUTSIDE.name,
        } | default_render_parameters

        super().__init__(
            class_,
            obj,
            render_styles=render_styles,
            default_render_parameters=default_render_parameters,
        )

    @property
    def name(self) -> str:
        return f"Context of {self.target.name.replace('/', '- or -')}"


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
    layer_sizing: t.Literal["UNION", "WIDTH", "HEIGHT", "INDIVIDUAL"],
) -> None:
    """Set `nodeSize.minimum` config in the layoutOptions."""

    def calculate_min(key: t.Literal["width", "height"] = "width") -> float:
        return max(getattr(child.size, key) for child in layout.children)  # type: ignore[union-attr]

    if layer_sizing not in {"UNION", "WIDTH", "HEIGHT", "INDIVIDUAL"}:
        raise NotImplementedError(
            "For ``layer_sizing`` only UNION, WIDTH, HEIGHT or INDIVIDUAL is supported"
        )

    min_w = calculate_min() + 15.0 if layer_sizing in {"UNION", "WIDTH"} else 0
    min_h = (
        calculate_min("height") if layer_sizing in {"UNION", "HEIGHT"} else 0
    )
    for layer in data.children:
        layer.layoutOptions["nodeSize.minimum"] = f"({min_w},{min_h})"


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
    padding: float = 10.0,
) -> tuple[float, float, float]:
    """Calculate the position of the label and tspan.

    The function calculates the center of the rectangle and uses the
    rectangle's width and height to adjust its position within it. The
    text is assumed to be horizontally and vertically centered within
    the rectangle. The tspan y coordinate is for positioning the label
    right under the left side of the rectangle.

    Parameters
    ----------
    x
        The x coordinate of the label position.
    y
        The y coordinate of the label position.
    width
        Width of the label.
    height
        Height of the label
    padding
        The padding for the label.

    Returns
    -------
    position
        A tuple containing the x- and y-coordinate for the text element
        and the adjusted y-coordinate for the tspan element.
    """
    center_y = y + height / 2
    tspan_y = center_y - width / 2 + padding
    return (x + width / 2, center_y, tspan_y)


def _get_all_ports(
    node: _elkjs.ELKOutputNode, ref: cdiagram.Vector2D
) -> cabc.Iterator[tuple[cdiagram.Vector2D, _elkjs.ELKOutputPort]]:
    """Yield all ports from."""
    for child in node.children:
        if isinstance(child, _elkjs.ELKOutputPort):
            yield ref + (child.position.x, child.position.y), child

        if isinstance(child, _elkjs.ELKOutputNode):
            yield from _get_all_ports(
                child, ref=ref + (child.position.x, child.position.y)
            )


def _calculate_middle(position, size, offset=None) -> _elkjs.ELKPoint:
    x = position.x + size.width / 2
    y = position.y + size.height / 2
    if offset:
        x += offset.x
        y += offset.y
    return _elkjs.ELKPoint(x=x, y=y)
