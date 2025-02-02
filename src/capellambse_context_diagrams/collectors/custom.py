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
import enum
import typing as t

import capellambse.model as m

from .. import _elkjs, context
from . import default, derived, generic, makers, portless


class EDGE_DIRECTION(enum.Enum):
    """Reroute direction of edges.

    Attributes
    ----------
    NONE
        No rerouting of edges.
    SMART
        Reroute edges to follow the primary direction of data flow.
    LEFT
        Edges are always placed on the left side.
    RIGHT
        Edges are always placed on the right side.
    TREE
        Reroute edges to follow a tree-like structure.
    """

    NONE = enum.auto()
    SMART = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    TREE = enum.auto()


def _is_edge(obj: m.ModelElement) -> bool:
    try:
        portless.collect_exchange_endpoints(obj)
        return True
    except AttributeError:
        return False


def _is_port(obj: m.ModelElement) -> bool:
    return obj.xtype.endswith("Port")


def get_uncommon_owner(
    src: m.ModelElement,
    tgt_owners: list[str],
) -> m.ModelElement:
    current = src
    while (
        hasattr(current, "owner")
        and current.owner is not None
        and current.owner.uuid not in tgt_owners
    ):
        current = current.owner
    return current


class CustomCollector:
    """Collect the context for a custom diagram."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.target: m.ModelElement = self.diagram.target

        self.boxable_target: m.ModelElement
        if _is_port(self.target):
            self.boxable_target = self.target.owner
        else:
            try:
                src, _ = portless.collect_exchange_endpoints(self.target)
                if self.diagram._is_portless:
                    self.boxable_target = src
                else:
                    self.boxable_target = src.owner
            except AttributeError:
                self.boxable_target = self.target

        self.data = makers.make_diagram(diagram)
        self.params = params
        self.collection = self.diagram._collect
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.boxes_to_delete: set[str] = set()
        self.edges_to_flip: dict[str, dict[bool, set[str]]] = {}
        self.min_heights: dict[str, dict[str, float]] = {}
        self.directions: dict[str, bool] = {}
        self.diagram_target_owners = list(
            generic.get_all_owners(self.boxable_target)
        )

        if self.diagram._display_parent_relation:
            self.edge_owners: dict[str, str] = {}
            self.common_owners: set[str] = set()

        if self.diagram._edge_direction in {
            EDGE_DIRECTION.RIGHT.name,
            EDGE_DIRECTION.LEFT.name,
            EDGE_DIRECTION.TREE.name,
        }:
            self.data.layoutOptions["layered.nodePlacement.strategy"] = (
                "NETWORK_SIMPLEX"
            )
        if self.diagram._edge_direction in {
            EDGE_DIRECTION.RIGHT.name,
            EDGE_DIRECTION.LEFT.name,
        }:
            self.directions[self.boxable_target.uuid] = (
                self.diagram._edge_direction == EDGE_DIRECTION.LEFT.name
            )

    def __call__(self) -> _elkjs.ELKInputData:
        if _is_port(self.target):
            port = self._make_port_and_owner("right", self.target)
            self._update_min_heights(self.boxable_target.uuid, "left", port)
        elif not _is_edge(self.target):
            self._make_box(self.target)
        elif self.diagram._display_target_edge:
            edge = self._make_edge_and_ports(self.target)
            assert edge is not None
            edge.layoutOptions = copy.deepcopy(
                _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
            )

        for elem in self.collection:
            self._make_target(elem)

        self._flip_edges()

        if self.diagram._display_parent_relation:
            current = self.boxable_target
            while (
                current
                and self.common_owners
                and getattr(current, "owner", None) is not None
                and not isinstance(current.owner, generic.PackageTypes)
            ):
                self.common_owners.discard(current.uuid)
                current = generic.make_owner_box(
                    current, self._make_box, self.boxes, self.boxes_to_delete
                )
                self.common_owners.discard(current.uuid)
            for edge_uuid, box_uuid in self.edge_owners.items():
                if box := self.boxes.get(box_uuid):
                    box.edges.append(self.edges.pop(edge_uuid))

        derivator = derived.DERIVATORS.get(type(self.target))
        if self.diagram._display_derived_interfaces and derivator is not None:
            derivator(self.diagram, self.boxes, self.edges)

        self._fix_box_heights()

        for uuid in self.boxes_to_delete:
            del self.boxes[uuid]

        return self._get_data()

    def _get_data(self) -> t.Any:
        if (
            self.diagram._hide_context_owner
            and len(self.boxes.values()) == 1
            and next(iter(self.boxes.values())) != self.boxable_target
        ):
            self.data.children = next(iter(self.boxes.values())).children
            self.data.edges = next(iter(self.boxes.values())).edges
        else:
            self.data.children = list(self.boxes.values())
            self.data.edges = list(self.edges.values())
        return self.data

    def _flip_edges(self) -> None:
        if self.diagram._edge_direction == EDGE_DIRECTION.NONE.name:
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

        if self.diagram._edge_direction == EDGE_DIRECTION.SMART.name:
            for edges in self.edges_to_flip.values():
                side = len(edges[True]) < len(edges[False])
                flip_side(edges, side)
        else:
            for edges in self.edges_to_flip.values():
                flip_side(edges, True)

    def _fix_box_heights(self) -> None:
        if self.diagram._edge_direction != EDGE_DIRECTION.NONE.name:
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max(box.height, sum(min_heights.values()))
        else:
            for uuid, min_heights in self.min_heights.items():
                box = self.boxes[uuid]
                box.height = max([box.height, *min_heights.values()])

    def _make_target(
        self, obj: m.ModelElement
    ) -> _elkjs.ELKInputChild | _elkjs.ELKInputEdge | None:
        if _is_edge(obj):
            return self._make_edge_and_ports(obj)
        return self._make_box(obj)

    def _make_box(
        self,
        obj: m.ModelElement,
        **kwargs: t.Any,
    ) -> _elkjs.ELKInputChild:
        if box := self.boxes.get(obj.uuid):
            return box
        box = makers.make_box(
            obj,
            no_symbol=self.diagram._display_symbols_as_boxes,
            slim_width=self.diagram._slim_center_box,
            **kwargs,
        )
        self.boxes[obj.uuid] = box
        if self.diagram._display_unused_ports:
            for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[
                self.diagram.type
            ]:
                for port_obj in getattr(obj, attr, []):
                    side = "left" if attr == "inputs" else "right"
                    self._make_port_and_owner(side, port_obj)
        if self.diagram._display_parent_relation:
            self.common_owners.add(
                generic.make_owner_boxes(
                    obj,
                    self.diagram_target_owners,
                    self._make_box,
                    self.boxes,
                    self.boxes_to_delete,
                )
            )
        return box

    def _make_edge_and_ports(
        self,
        edge_obj: m.ModelElement,
    ) -> _elkjs.ELKInputEdge | None:
        if self.edges.get(edge_obj.uuid):
            return None

        ex_data = generic.ExchangeData(
            edge_obj,
            self.data,
            self.diagram.filters,
            self.params,
        )

        src_obj: m.ModelElement | None
        tgt_obj: m.ModelElement | None

        if self.diagram._is_portless:
            src_owner, tgt_owner = generic.exchange_data_collector(
                ex_data, portless.collect_exchange_endpoints
            )
            src_obj, tgt_obj = None, None
            edge = self.data.edges.pop()
        else:
            src_obj, tgt_obj = generic.exchange_data_collector(ex_data)
            src_owner, tgt_owner = src_obj.owner, tgt_obj.owner
            edge = self.data.edges.pop()

            if self.diagram._mode == default.MODE.GRAYBOX.name:

                def get_unc(obj):
                    if self.boxable_target.uuid in generic.get_all_owners(obj):
                        return self.boxable_target
                    return get_uncommon_owner(obj, self.diagram_target_owners)

                src_unc, tgt_unc = get_unc(src_owner), get_unc(tgt_owner)
                if src_unc.uuid == tgt_unc.uuid:
                    return None
                if src_unc.uuid != src_owner.uuid:
                    edge.id = f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{edge.id}"
                    src_owner = src_unc
                if tgt_unc.uuid != tgt_owner.uuid:
                    edge.id = f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{edge.id}"
                    tgt_owner = tgt_unc

        src_owners = list(generic.get_all_owners(src_owner))
        tgt_owners = list(generic.get_all_owners(tgt_owner))

        if (
            self.diagram._hide_direct_children
            and self.boxable_target.uuid in src_owners
            and self.boxable_target.uuid in tgt_owners
        ):
            return None

        self._make_port_and_owner("right", src_obj, src_owner)
        self._make_port_and_owner("left", tgt_obj, tgt_owner)

        if self.diagram._display_parent_relation:
            common_owner = None
            for owner in src_owners:
                if owner in tgt_owners:
                    common_owner = owner
                    break
            if common_owner:
                self.edge_owners[edge_obj.uuid] = common_owner

        flip_needed, unc = self._need_flip(
            src_owner,
            tgt_owner,
            src_owners,
            tgt_owners,
        )
        self.edges_to_flip.setdefault(unc, {True: set(), False: set()})[
            flip_needed
        ].add(edge_obj.uuid)

        self.edges[edge_obj.uuid] = edge
        return edge

    def _update_min_heights(
        self,
        owner_uuid: str,
        side: str,
        port: _elkjs.ELKInputPort | None = None,
    ) -> None:
        height: int | float
        if port is None:
            height = 2 * generic.MARKER_PADDING + generic.MARKER_SIZE
        else:
            height = makers.PORT_SIZE + max(
                2 * makers.PORT_PADDING,
                sum(label.height for label in port.labels),
            )
        self.min_heights.setdefault(owner_uuid, {"left": 0.0, "right": 0.0})[
            side
        ] += height

    def _need_flip(
        self,
        src: m.ModelElement,
        tgt: m.ModelElement,
        src_owners: list[str],
        tgt_owners: list[str],
    ) -> tuple[bool, str]:
        if self.diagram._edge_direction == EDGE_DIRECTION.NONE.name:
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
            uncommon_owner = get_uncommon_owner(obj, opposite_owners)
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
        if edge_direction == EDGE_DIRECTION.SMART.name:
            src_dir, src_unc = _get_direction(src, tgt_owners, False)
            tgt_dir, tgt_unc = _get_direction(tgt, src_owners, True)
            return src_dir is True or tgt_dir is False, (src_unc or tgt_unc)

        _, tgt_dir = _initialize_directions(
            edge_direction != EDGE_DIRECTION.RIGHT.name,
            edge_direction != EDGE_DIRECTION.LEFT.name,
        )
        if edge_direction == EDGE_DIRECTION.TREE.name:
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
            layout_options=makers.CENTRIC_LABEL_LAYOUT_OPTIONS,
        )
        port: _elkjs.ELKInputPort | None
        if port_obj is None:
            port = None
        else:
            if port := self.ports.get(port_obj.uuid):
                return port
            port = makers.make_port(port_obj.uuid)
            if self.diagram._display_port_labels:
                text = port_obj.name or "UNKNOWN"
                port.labels = makers.make_label(text)
                _plp = self.diagram._port_label_position
                if not (
                    plp := getattr(_elkjs.PORT_LABEL_POSITION, _plp, None)
                ):
                    raise ValueError(f"Invalid port label position '{_plp}'.")
                assert isinstance(plp, _elkjs.PORT_LABEL_POSITION)
                box.layoutOptions["portLabels.placement"] = plp.name
            box.ports.append(port)
            self.ports[port_obj.uuid] = port
        self._update_min_heights(owner_obj.uuid, side, port)
        return port


def collector(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """High level collector function to collect needed data for ELK.

    Parameters
    ----------
    diagram
        The [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram]
        instance to get the
        [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
        for.
    params
        Optional render params dictionary.

    Returns
    -------
    elkdata
        The data that can be fed into elkjs.
    """
    return CustomCollector(diagram, params)()
