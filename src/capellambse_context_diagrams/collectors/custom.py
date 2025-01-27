# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Collector for the CustomDiagram."""

from __future__ import annotations

import collections.abc as cabc
import copy
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa, la, sa

from .. import _elkjs, context
from . import generic, makers

if t.TYPE_CHECKING:
    from .. import context

    DerivatorFunction: t.TypeAlias = cabc.Callable[
        [
            context.CustomDiagram,
            dict[str, _elkjs.ELKInputChild],
            dict[str, _elkjs.ELKInputEdge],
        ],
        None,
    ]

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]


def _is_edge(obj: m.ModelElement) -> bool:
    return hasattr(obj, "source") and hasattr(obj, "target")


def _is_port(obj: m.ModelElement) -> bool:
    return obj.xtype.endswith("Port")


class CustomCollector:
    """Collect the context for a custom diagram."""

    def __init__(
        self,
        diagram: context.CustomDiagram,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.target: m.ModelElement = self.diagram.target

        self.boxable_target: m.ModelElement
        if _is_port(self.target):
            self.boxable_target = self.target.owner
        elif _is_edge(self.target):
            self.boxable_target = self.target.source.owner
        else:
            self.boxable_target = self.target

        self.data = makers.make_diagram(diagram)
        self.params = params
        self.collection = self.diagram._collect
        self.boxes: dict[str, _elkjs.ELKInputChild] = {}
        self.edges: dict[str, _elkjs.ELKInputEdge] = {}
        self.ports: dict[str, _elkjs.ELKInputPort] = {}
        self.boxes_to_delete: set[str] = set()
        self.edges_to_flip: dict[str, dict[bool, set[str]]] = {}

        if self.diagram._display_parent_relation:
            self.edge_owners: dict[str, str] = {}
            self.common_owners: set[str] = set()

        if self.diagram._display_parent_relation or self.diagram._blackbox:
            self.diagram_target_owners = list(
                generic.get_all_owners(self.boxable_target)
            )

        if self.diagram._unify_edge_direction != "NONE":
            self.directions: dict[str, bool] = {}

        if self.diagram._unify_edge_direction == "UNIFORM":
            self.directions[self.boxable_target.uuid] = False

        self.min_heights: dict[str, dict[str, float]] = {}

    def __call__(self) -> _elkjs.ELKInputData:
        if _is_port(self.target):
            port = self._make_port_and_owner(self.target, "right")
            self._update_min_heights(self.boxable_target.uuid, "left", port)
        else:
            self._make_target(self.target)

        if target_edge := self.edges.get(self.target.uuid):
            target_edge.layoutOptions = copy.deepcopy(
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

        derivator = DERIVATORS.get(type(self.target))
        if self.diagram._display_derived_interfaces and derivator is not None:
            derivator(self.diagram, self.boxes, self.edges)

        self._fix_box_heights()
        for uuid in self.boxes_to_delete:
            del self.boxes[uuid]
        return self._get_data()

    def _get_data(self) -> t.Any:
        self.data.children = list(self.boxes.values())
        self.data.edges = list(self.edges.values())
        return self.data

    def _flip_edges(self) -> None:
        if self.diagram._unify_edge_direction == "NONE":
            return

        def flip(edge_uuid: str) -> None:
            edge = self.edges[edge_uuid]
            edge.sources[-1], edge.targets[-1] = (
                edge.targets[-1],
                edge.sources[-1],
            )

        def flip_small_side(edges: dict[bool, set[str]]) -> None:
            side = len(edges[True]) < len(edges[False])
            for edge_uuid in edges[side]:
                flip(edge_uuid)

        for edges in self.edges_to_flip.values():
            flip_small_side(edges)

    def _fix_box_heights(self) -> None:
        if self.diagram._unify_edge_direction != "NONE":
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
        return self._make_box(obj, slim_width=self.diagram._slim_center_box)

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
            **kwargs,
        )
        self.boxes[obj.uuid] = box
        if self.diagram._display_unused_ports:
            for attr in generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[
                self.diagram.type
            ]:
                for port_obj in getattr(obj, attr, []):
                    side = "left" if attr == "inputs" else "right"
                    self._make_port_and_owner(port_obj, side)
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
        src_obj, tgt_obj = generic.exchange_data_collector(ex_data)
        edge = self.data.edges.pop()
        src_owner = src_obj.owner
        tgt_owner = tgt_obj.owner
        src_owners = list(generic.get_all_owners(src_obj))
        tgt_owners = list(generic.get_all_owners(tgt_obj))
        is_src = self.boxable_target.uuid in src_owners
        is_tgt = self.boxable_target.uuid in tgt_owners

        if self.diagram._blackbox:
            if is_src and is_tgt:
                return None
            if is_src and src_owner.uuid != self.boxable_target.uuid:
                edge.id = (
                    f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{edge.id}"
                )
                src_owner = self.boxable_target
                src_owners = self.diagram_target_owners
            elif is_tgt and tgt_owner.uuid != self.boxable_target.uuid:
                edge.id = (
                    f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{edge.id}"
                )
                tgt_owner = self.boxable_target
                tgt_owners = self.diagram_target_owners

        if self.diagram._display_parent_relation:
            common_owner = None
            for owner in src_owners:
                if owner in tgt_owners:
                    common_owner = owner
                    break
            if common_owner:
                self.edge_owners[edge_obj.uuid] = common_owner

        flip_needed, unc = self._need_flip(
            src_owners, tgt_owners, src_owner.uuid, tgt_owner.uuid
        )
        self.edges_to_flip.setdefault(unc, {True: set(), False: set()})[
            flip_needed
        ].add(edge_obj.uuid)
        if flip_needed:
            src_obj, tgt_obj = tgt_obj, src_obj
            src_owner, tgt_owner = tgt_owner, src_owner
            is_src, is_tgt = is_tgt, is_src

        if not self.ports.get(src_obj.uuid):
            self._make_port_and_owner(src_obj, "right", src_owner)
        if not self.ports.get(tgt_obj.uuid):
            self._make_port_and_owner(tgt_obj, "left", tgt_owner)

        self.edges[edge_obj.uuid] = edge
        return edge

    def _update_min_heights(
        self, owner_uuid: str, side: str, port: _elkjs.ELKInputPort
    ) -> None:
        self.min_heights.setdefault(owner_uuid, {"left": 0.0, "right": 0.0})[
            side
        ] += makers.PORT_SIZE + max(
            2 * makers.PORT_PADDING,
            sum(label.height for label in port.labels),
        )

    def _need_flip(
        self,
        src_owners: list[str],
        tgt_owners: list[str],
        src_uuid: str,
        tgt_uuid: str,
    ) -> tuple[bool, str]:
        def _get_direction(
            uuid: str,
            owners: list[str],
            opposite_owners: list[str],
            default: bool,
        ) -> tuple[bool | None, str]:
            if uuid == self.boxable_target.uuid:
                return None, ""
            uncommon_owner = [
                owner for owner in owners if owner not in opposite_owners
            ][-1]
            return (
                self.directions.setdefault(uncommon_owner, default),
                uncommon_owner,
            )

        def _initialize_directions(
            src_uuid: str, tgt_uuid: str, default_src: bool, default_tgt: bool
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

        edge_direction: str = self.diagram._unify_edge_direction
        if edge_direction == "SMART":
            src_dir, src_unc = _get_direction(
                src_uuid, src_owners, tgt_owners, False
            )
            tgt_dir, tgt_unc = _get_direction(
                tgt_uuid, tgt_owners, src_owners, True
            )
            return src_dir is True or tgt_dir is False, (src_unc or tgt_unc)

        if edge_direction == "UNIFORM":
            src_dir, _ = _initialize_directions(
                src_uuid, tgt_uuid, False, True
            )
            return self.directions[src_uuid], self.boxable_target.uuid

        if edge_direction == "TREE":
            src_dir, tgt_dir = _initialize_directions(
                src_uuid, tgt_uuid, True, True
            )
            return tgt_dir is not None, self.boxable_target.uuid

        return False, self.boxable_target.uuid

    def _make_port_and_owner(
        self,
        port_obj: m.ModelElement,
        side: str,
        owner: m.ModelElement | None = None,
    ) -> _elkjs.ELKInputPort:
        owner_obj = owner if owner else port_obj.owner
        box = self._make_box(
            owner_obj,
            layout_options=makers.CENTRIC_LABEL_LAYOUT_OPTIONS,
        )
        if port := self.ports.get(port_obj.uuid):
            return port
        port = makers.make_port(port_obj.uuid)
        if self.diagram._display_port_labels:
            text = port_obj.name or "UNKNOWN"
            port.labels = makers.make_label(text)
            _plp = self.diagram._port_label_position
            if not (plp := getattr(_elkjs.PORT_LABEL_POSITION, _plp, None)):
                raise ValueError(f"Invalid port label position '{_plp}'.")
            assert isinstance(plp, _elkjs.PORT_LABEL_POSITION)
            box.layoutOptions["portLabels.placement"] = plp.name
        box.ports.append(port)
        self.ports[port_obj.uuid] = port
        self._update_min_heights(owner_obj.uuid, side, port)
        return port


def collector(
    diagram: context.CustomDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    """Collect data for rendering a custom diagram."""
    return CustomCollector(diagram, params)()


def derive_from_functions(
    diagram: context.CustomDiagram,
    boxes: dict[str, _elkjs.ELKInputChild],
    edges: dict[str, _elkjs.ELKInputEdge],
) -> None:
    """Derive Components from allocated functions of the context target.

    A Component, a ComponentExchange and two ComponentPorts are added
    to ``data``. These elements are prefixed with ``Derived-`` to
    receive special styling in the serialization step.
    """
    assert isinstance(diagram.target, cs.Component)
    ports: list[m.ModelElement] = []
    for fnc in diagram.target.allocated_functions:
        inc, out = generic.port_collector(fnc, diagram.type)
        ports.extend((inc | out).values())

    derived_components: dict[str, cs.Component] = {}
    for port in ports:
        for fex in port.exchanges:
            if isinstance(port, fa.FunctionOutputPort):
                attr = "target"
            else:
                attr = "source"

            try:
                derived_comp = getattr(fex, attr).owner.owner
                if (
                    derived_comp == diagram.target
                    or derived_comp.uuid in boxes
                ):
                    continue

                if derived_comp.uuid not in derived_components:
                    derived_components[derived_comp.uuid] = derived_comp
            except AttributeError:  # No owner of owner.
                pass

    # Idea: Include flow direction of derived interfaces from all functional
    # exchanges. Mixed means bidirectional. Just even out bidirectional
    # interfaces and keep flow direction of others.

    centerbox = boxes[diagram.target.uuid]
    i = 0
    for i, (uuid, derived_component) in enumerate(
        derived_components.items(), 1
    ):
        box = makers.make_box(
            derived_component,
            no_symbol=diagram._display_symbols_as_boxes,
        )
        class_ = diagram.serializer.get_styleclass(derived_component.uuid)
        box.id = f"{makers.STYLECLASS_PREFIX}-{class_}:{uuid}"
        boxes[uuid] = box
        source_id = f"{makers.STYLECLASS_PREFIX}-CP_INOUT:{i}"
        target_id = f"{makers.STYLECLASS_PREFIX}-CP_INOUT:{-i}"
        box.ports.append(makers.make_port(source_id))
        centerbox.ports.append(makers.make_port(target_id))
        if i % 2 == 0:
            source_id, target_id = target_id, source_id

        uid = f"{makers.STYLECLASS_PREFIX}-ComponentExchange:{i}"
        edges[uid] = _elkjs.ELKInputEdge(
            id=uid,
            sources=[source_id],
            targets=[target_id],
        )

    centerbox.height += (
        makers.PORT_PADDING + (makers.PORT_SIZE + makers.PORT_PADDING) * i // 2
    )


DERIVATORS: dict[type[m.ModelElement], DerivatorFunction] = {
    la.LogicalComponent: derive_from_functions,
    sa.SystemComponent: derive_from_functions,
}
"""Supported objects to build derived contexts for."""
