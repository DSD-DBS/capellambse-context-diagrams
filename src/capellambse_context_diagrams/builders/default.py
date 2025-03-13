# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Build an ELK diagram from collected capellambse context.

This submodule provides a collector that transforms capellambse data to an ELK-
layouted diagram
[_elkjs.ELKInputData][capellambse_context_diagrams._elkjs.ELKInputData].

The data was collected with the functions from
[collectors][capellambse_context_diagrams.collectors].
"""

from __future__ import annotations

import copy
import dataclasses
import typing as t

import capellambse.model as m
from capellambse.metamodel import fa

from .. import _elkjs, context, enums
from ..collectors import _generic, portless
from . import _makers, derived


@dataclasses.dataclass
class ConnectorData:
    port: m.ModelElement | None
    owner: m.ModelElement
    is_source: bool
    remove_port: bool = False
    owners: list[str] = dataclasses.field(init=False, default_factory=list)

    def __post_init__(self):
        self.owners = list(_generic.get_all_owners(self.port or self.owner))


@dataclasses.dataclass
class EdgeData:
    obj: m.ModelElement
    edge: _elkjs.ELKInputEdge
    source: ConnectorData
    target: ConnectorData


def _is_edge(obj: m.ModelElement) -> bool:
    try:
        portless.collect_exchange_endpoints(obj)
        return True
    except AttributeError:
        return False


def _is_port(obj: m.ModelElement) -> bool:
    return obj.xtype.endswith("Port")


def get_top_uncommon_owner(
    src: m.ModelElement, tgt_owners: list[str]
) -> m.ModelElement:
    """Return the top-level owner of ``src`` not in ``tgt_owners``."""
    current = src
    while (
        hasattr(current, "owner")
        and current.owner is not None
        and current.owner.uuid not in tgt_owners
    ):
        current = current.owner
    return current


def _get_boxeable_target(diagram: context.ContextDiagram) -> m.ModelElement:
    if _is_port(diagram.target):
        return diagram.target.owner
    try:
        src, _ = portless.collect_exchange_endpoints(diagram.target)
        if diagram._is_portless:
            return src
        return src.owner
    except AttributeError:
        return diagram.target


class DiagramBuilder:
    """Collect the context for a ContextDiagram."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.collection = self.diagram._collect(self.diagram)
        self.target: m.ModelElement = self.diagram.target
        self.boxable_target = _get_boxeable_target(self.diagram)
        self.data = _makers.make_diagram(diagram)
        self.params = params
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.boxes_to_delete: set[str] = set()
        self.edges_to_flip: dict[str, dict[bool, set[str]]] = {}
        self.min_heights: dict[str, dict[str, float]] = {}
        self.directions: dict[str, bool] = {}
        self.diagram_target_owners = list(
            _generic.get_all_owners(self.boxable_target)
        )

        if self.diagram._display_parent_relation:
            self.edge_owners: dict[str, str] = {}
            self.common_owners: set[str] = set()

        if self.diagram._edge_direction in {
            enums.EDGE_DIRECTION.RIGHT,
            enums.EDGE_DIRECTION.LEFT,
            enums.EDGE_DIRECTION.TREE,
        }:
            self.data.layoutOptions["layered.nodePlacement.strategy"] = (
                "NETWORK_SIMPLEX"
            )
        if self.diagram._edge_direction in {
            enums.EDGE_DIRECTION.RIGHT,
            enums.EDGE_DIRECTION.LEFT,
        }:
            self.directions[self.boxable_target.uuid] = (
                self.diagram._edge_direction == enums.EDGE_DIRECTION.LEFT
            )

    def __call__(self) -> _elkjs.ELKInputData:
        self._handle_boxeable_target()

        for elem in self.collection:
            if self.diagram._mode == enums.MODE.BLACKBOX:
                self._make_blackbox_target(elem)
            elif self.diagram._mode == enums.MODE.WHITEBOX:
                self._make_whitebox_target(elem)

        self._flip_edges()
        self._resolve_parent_relationship()

        derivator = derived.DERIVATORS.get(type(self.target))
        if self.diagram._display_derived_interfaces and derivator is not None:
            derivator(self.diagram, self.boxes, self.edges)

        self._fix_box_heights()

        for uuid in self.boxes_to_delete:
            del self.boxes[uuid]

        return self._get_data()

    def _handle_boxeable_target(self) -> None:
        if _is_port(self.target):
            port = self._make_port_and_owner("right", self.target)
            self._update_min_heights(self.boxable_target.uuid, "left", port)
        elif not _is_edge(self.target):
            self._make_box(self.target, no_symbol=self.diagram._is_portless)
        elif self.diagram._include_interface or self.diagram._hide_functions:
            edge = self._make_edge_and_ports(self.target)
            assert edge is not None
            edge.layoutOptions = copy.deepcopy(
                _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
            )

    def _resolve_parent_relationship(self) -> None:
        if (
            self.diagram._display_parent_relation
            or self.diagram._display_functional_parent_relation
        ):
            current = self.boxable_target
            while (
                current
                and self.common_owners
                and getattr(current, "owner", None) is not None
                and not isinstance(current.owner, _makers.PackageTypes)
            ):
                self.common_owners.discard(current.uuid)
                current = _makers.make_owner_box(
                    current, self._make_box, self.boxes, self.boxes_to_delete
                )
                self.common_owners.discard(current.uuid)
            for edge_uuid, box_uuid in self.edge_owners.items():
                if box := self.boxes.get(box_uuid):
                    box.edges.append(self.edges.pop(edge_uuid))

        if self.diagram._display_functional_parent_relation:
            for uuid, box in self.boxes.items():
                element = self.target._model.by_uuid(uuid)
                if isinstance(element, fa.AbstractFunction) and (
                    parent_box := self.boxes.get(element.parent.uuid)
                ):
                    if owner_box := self.boxes.get(element.owner.uuid):
                        owner_box.children.remove(box)
                    parent_box.children.append(box)

    def _get_data(self) -> _elkjs.ELKInputData:
        safe_to_hide = False
        if (
            self.diagram._hide_context_owner
            and len(self.boxes.values()) == 1
            and (context_owner := next(iter(self.boxes.values())))
            != self.boxable_target
        ):
            deleted_ports = {port.id for port in context_owner.ports}
            for edge in context_owner.edges:
                if {edge.sources[0], edge.targets[0]} & deleted_ports:
                    break
            else:
                safe_to_hide = True

        if safe_to_hide and context_owner.children and context_owner.edges:
            self.data.children = context_owner.children
            self.data.edges = context_owner.edges
        else:
            self.data.children = list(self.boxes.values())
            self.data.edges = list(self.edges.values())
        return self.data

    def _flip_edges(self) -> None:
        if self.diagram._edge_direction == enums.EDGE_DIRECTION.NONE:
            return

        def flip(edge_uuid: str) -> None:
            edge = self.edges[edge_uuid]
            edge.sources[-1], edge.targets[-1] = (
                edge.targets[-1],
                edge.sources[-1],
            )

        def flip_side(edges: dict[bool, set[str]], side: bool) -> None:
            for edge_uuid in edges[side]:
                flip(edge_uuid)

        if self.diagram._edge_direction == enums.EDGE_DIRECTION.SMART:
            for edges in self.edges_to_flip.values():
                side = len(edges[True]) < len(edges[False])
                flip_side(edges, side)
        else:
            for edges in self.edges_to_flip.values():
                flip_side(edges, True)

    def _fix_box_heights(self) -> None:
        if self.diagram._edge_direction != enums.EDGE_DIRECTION.NONE:
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max(box.height, sum(min_heights.values()))
        else:
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max([box.height, *min_heights.values()])

    def _make_box(
        self,
        obj: m.ModelElement,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        if box := self.boxes.get(obj.uuid):
            return box
        no_symbol = (
            kwargs.pop("no_symbol", False)
            or self.diagram._display_symbols_as_boxes
        )
        box = _makers.make_box(
            obj,
            no_symbol=no_symbol,
            slim_width=self.diagram._slim_center_box,
            **kwargs,
        )
        self.boxes[obj.uuid] = box
        if self.diagram._display_unused_ports:
            for attr in _generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[
                self.diagram.type
            ]:
                for port_obj in getattr(obj, attr, []):
                    side = "left" if attr == "inputs" else "right"
                    self._make_port_and_owner(side, port_obj)

        if self.diagram._display_parent_relation:
            self.common_owners.add(
                _makers.make_owner_boxes(
                    obj,
                    self.diagram_target_owners,
                    self._make_box,
                    self.boxes,
                    self.boxes_to_delete,
                )
            )
        return box

    def _update_min_heights(
        self,
        owner_uuid: str,
        side: str,
        port: _elkjs.ELKInputPort | None = None,
    ) -> None:
        height: int | float
        if port is None:
            height = 2 * _generic.MARKER_PADDING + _generic.MARKER_SIZE
        else:
            height = _makers.PORT_SIZE + max(
                2 * _makers.PORT_PADDING,
                sum(label.height for label in port.labels),
            )

        box = self.boxes[owner_uuid]
        self.min_heights.setdefault(box.id, {"left": 0.0, "right": 0.0})[
            side
        ] += height

    def _need_flip(
        self,
        src: m.ModelElement,
        tgt: m.ModelElement,
        src_owners: list[str],
        tgt_owners: list[str],
    ) -> tuple[bool, str]:
        if self.diagram._edge_direction == enums.EDGE_DIRECTION.NONE:
            return False, self.boxable_target.uuid

        src_uuid = src.uuid
        tgt_uuid = tgt.uuid

        def _get_direction(
            obj: m.ModelElement,
            opposite_owners: list[str],
            default: bool,
        ) -> tuple[bool | None, str]:
            if obj.uuid == self.boxable_target.uuid:
                return None, ""
            uncommon_owner = get_top_uncommon_owner(obj, opposite_owners)
            return (
                self.directions.setdefault(uncommon_owner.uuid, default),
                uncommon_owner.uuid,
            )

        def _initialize_directions(
            default_src: bool, default_tgt: bool
        ) -> tuple[bool | None, bool | None]:
            src_dir = self.directions.get(src_uuid)
            tgt_dir = self.directions.get(tgt_uuid)
            if src_dir is None and tgt_dir is None:
                self.directions[src_uuid] = default_src
                self.directions[tgt_uuid] = default_tgt
            elif src_dir is None:
                self.directions[src_uuid] = not tgt_dir
            elif tgt_dir is None:
                self.directions[tgt_uuid] = not src_dir

            return src_dir, tgt_dir

        edge_direction = self.diagram._edge_direction
        if edge_direction == enums.EDGE_DIRECTION.SMART:
            src_dir, src_unc = _get_direction(src, tgt_owners, False)
            tgt_dir, tgt_unc = _get_direction(tgt, src_owners, True)
            return src_dir is True or tgt_dir is False, (src_unc or tgt_unc)

        _, tgt_dir = _initialize_directions(
            edge_direction != enums.EDGE_DIRECTION.RIGHT,
            edge_direction != enums.EDGE_DIRECTION.LEFT,
        )
        if edge_direction == enums.EDGE_DIRECTION.TREE:
            return tgt_dir is not None, self.boxable_target.uuid
        return self.directions[src_uuid], self.boxable_target.uuid

    def _make_port_and_owner(
        self,
        side: str,
        port_obj: m.ModelElement | None = None,
        owner: m.ModelElement | None = None,
    ) -> _elkjs.ELKInputPort | None:
        owner_obj = owner or port_obj.owner  # type: ignore
        box = self._make_box(
            owner_obj,
            layout_options=_makers.CENTRIC_LABEL_LAYOUT_OPTIONS,
        )
        port: _elkjs.ELKInputPort | None
        if port_obj is None:
            port = None
        else:
            if port := self.ports.get(port_obj.uuid):
                return port
            port = _makers.make_port(port_obj.uuid)
            if self.diagram._display_port_labels:
                text = port_obj.name or "UNKNOWN"
                port.labels = _makers.make_label(text)
                if isinstance(plp := self.diagram._port_label_position, str):
                    try:
                        plp = _elkjs.PORT_LABEL_POSITION[plp]
                    except KeyError:
                        raise ValueError(
                            f"Invalid port label position '{plp}'."
                        ) from None
                elif not isinstance(plp, _elkjs.PORT_LABEL_POSITION):
                    raise ValueError(f"Invalid port label position: {plp!r}")

                assert isinstance(plp, _elkjs.PORT_LABEL_POSITION)
                box.layoutOptions["portLabels.placement"] = plp.name
            box.ports.append(port)
            self.ports[port_obj.uuid] = port
        self._update_min_heights(owner_obj.uuid, side, port)
        return port

    def _is_inside_noi(self, element: m.ModelElement) -> bool:
        return self.boxable_target.uuid in set(
            _generic.get_all_owners(element)
        )

    def _collect_edge_data(self, edge_obj: m.ModelElement) -> EdgeData:
        ex_data = _generic.ExchangeData(
            edge_obj, self.data, self.diagram.filters, self.params
        )
        if self.diagram._is_portless:
            src_owner, tgt_owner = _generic.exchange_data_collector(
                ex_data, portless.collect_exchange_endpoints
            )
            src_obj = tgt_obj = None
        else:
            src_obj, tgt_obj = _generic.exchange_data_collector(ex_data)
            src_owner, tgt_owner = src_obj.owner, tgt_obj.owner

        edge = self.data.edges.pop()
        return EdgeData(
            edge_obj,
            edge,
            ConnectorData(src_obj, src_owner, True),
            ConnectorData(tgt_obj, tgt_owner, False),
        )

    def _update_edge_common(
        self, edge_data: EdgeData
    ) -> _elkjs.ELKInputEdge | None:
        """Update ports, parent relation, and edge flip settings."""
        src_owners = edge_data.source.owners
        tgt_owners = edge_data.target.owners

        if edge_data.source.remove_port:
            self._make_port_and_owner(
                "left", port_obj=None, owner=edge_data.source.owner
            )
            edge_data.edge.sources[-1] = edge_data.source.owner.uuid
        else:
            self._make_port_and_owner(
                "left", edge_data.source.port, edge_data.source.owner
            )

        if edge_data.target.remove_port:
            self._make_port_and_owner(
                "right", port_obj=None, owner=edge_data.target.owner
            )
            edge_data.edge.targets[-1] = edge_data.target.owner.uuid
        else:
            self._make_port_and_owner(
                "right", edge_data.target.port, edge_data.target.owner
            )

        if self.diagram._display_parent_relation:
            common_owner = None
            if edge_data.source.owner == edge_data.target.owner:
                common_owner = getattr(
                    edge_data.source.owner.owner, "uuid", None
                )
            else:
                for owner in src_owners:
                    if owner in tgt_owners:
                        common_owner = owner
                        break
            if common_owner:
                self.edge_owners[edge_data.obj.uuid] = common_owner

        flip_needed, unc = self._need_flip(
            edge_data.source.owner,
            edge_data.target.owner,
            src_owners,
            tgt_owners,
        )
        self.edges_to_flip.setdefault(unc, {True: set(), False: set()})[
            flip_needed
        ].add(edge_data.obj.uuid)
        self.edges[edge_data.obj.uuid] = edge_data.edge
        return edge_data.edge

    def _apply_internal_adjustment(
        self,
        edge_data: EdgeData,
        src_override: m.ModelElement,
        tgt_override: m.ModelElement,
        class_name: str,
    ) -> None:
        if src_override.uuid != edge_data.source.owner.uuid:
            edge_data.edge.id = f"{_makers.STYLECLASS_PREFIX}-{class_name}:{edge_data.obj.uuid}"
            edge_data.source.owner = src_override
            edge_data.source.remove_port = True
        if tgt_override.uuid != edge_data.target.owner.uuid:
            edge_data.edge.id = f"{_makers.STYLECLASS_PREFIX}-{class_name}:{edge_data.obj.uuid}"
            edge_data.target.owner = tgt_override
            edge_data.target.remove_port = True

    def _make_edge_and_ports(
        self, edge_obj: m.ModelElement, edge_data: EdgeData | None = None
    ) -> _elkjs.ELKInputEdge | None:
        if self.edges.get(edge_obj.uuid):
            return None

        if edge_data is None:
            edge_data = self._collect_edge_data(edge_obj)

        if (
            (not _is_edge(self.target) and not _is_port(self.target))
            and not self._is_inside_noi(edge_data.source.owner)
            and not self._is_inside_noi(edge_data.target.owner)
            and not self.diagram._include_external_context
        ):
            return None
        return self._update_edge_common(edge_data)

    def _make_whitebox_target(
        self, obj: m.ModelElement
    ) -> _elkjs.ELKInputChild | _elkjs.ELKInputEdge | None:
        if _is_edge(obj):
            return self._make_edge_and_ports(obj)
        return self._make_box(obj)

    def _make_blackbox_target(self, obj: m.ModelElement) -> None:
        edge_data = self._collect_edge_data(obj)

        src_override: m.ModelElement | None = None
        assert edge_data.source.port is not None
        if self._is_inside_noi(edge_data.source.port):
            src_override = self.boxable_target
        elif not self.diagram._include_external_context:
            src_override = get_top_uncommon_owner(
                edge_data.source.owner, self.diagram_target_owners
            )

        tgt_override: m.ModelElement | None = None
        assert edge_data.target.port is not None
        if self._is_inside_noi(edge_data.target.port):
            tgt_override = self.boxable_target
        elif not self.diagram._include_external_context:
            tgt_override = get_top_uncommon_owner(
                edge_data.target.owner, self.diagram_target_owners
            )

        allow_internal = self.diagram._display_internal_relations
        allow_cycle = self.diagram._display_cyclic_relations
        cycle = self._is_cycle(src_override, tgt_override)
        internal = self._is_external_internal(
            src_override, tgt_override, edge_data
        )
        if (internal and not allow_internal) or (cycle and not allow_cycle):
            return

        if internal and not allow_internal:
            return

        if src_override or tgt_override:
            self._apply_internal_adjustment(
                edge_data,
                src_override or edge_data.source.owner,
                tgt_override or edge_data.target.owner,
                type(obj).__name__,
            )

        self._make_edge_and_ports(obj, edge_data=edge_data)
        return

    def _is_cycle(
        self, source: m.ModelElement | None, target: m.ModelElement | None
    ) -> bool:
        return bool(source and source == target)

    def _is_external_internal(
        self,
        source: m.ModelElement | None,
        target: m.ModelElement | None,
        edge_data: EdgeData,
    ) -> bool:
        """Check if edge connects to the inside of source or target."""
        return bool(
            (source and source.uuid != edge_data.source.owner.uuid)
            or (target and target.uuid != edge_data.target.owner.uuid)
        )


def builder(
    diagram: context.ContextDiagram,
    params: dict[str, t.Any],
    builder_type: type[DiagramBuilder] = DiagramBuilder,
) -> _elkjs.ELKInputData:
    """High level builder function to build collected data for ELK.

    Parameters
    ----------
    diagram
        The [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram]
        instance to get the
        [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
        for.
    params
        Optional render params dictionary.
    builder_type
        The type of diagram builder to use.

    Returns
    -------
    elkdata
        The data that can be fed into elkjs.
    """
    return builder_type(diagram, params)()
