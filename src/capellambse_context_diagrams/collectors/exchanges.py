# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import copy
import logging
import operator
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa
from capellambse.model import DiagramType as DT

from .. import _elkjs, context, errors
from . import generic, makers

logger = logging.getLogger(__name__)


class ExchangeCollector(metaclass=abc.ABCMeta):
    """Base class for context collection on Exchanges."""

    intermap: t.ClassVar[dict[DT, tuple[str, str, str, str]]] = {
        DT.OAB: ("source", "target", "allocated_interactions", "activities"),
        DT.SAB: (
            "source.owner",
            "target.owner",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
        DT.LAB: (
            "source.owner",
            "target.owner",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
        DT.PAB: (
            "source.owner",
            "target.owner",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
    }

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram
        | context.FunctionalContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        self.diagram = diagram
        self.data: _elkjs.ELKInputData = data
        self.obj = self.diagram.target
        self.params = params

        src, trg, alloc_fex, fncs = self.intermap[diagram.type]
        self.get_source = operator.attrgetter(src)
        self.get_target = operator.attrgetter(trg)
        self.get_alloc_fex = operator.attrgetter(alloc_fex)
        self.get_alloc_functions = operator.attrgetter(fncs)

    def update_children_size(
        self,
        data: _elkjs.ELKInputChild,
        exchanges: t.Sequence[_elkjs.ELKInputEdge],
    ) -> None:
        """Adjust size of functions."""
        stack_height: int | float = -makers.NEIGHBOR_VMARGIN
        for child in data.children:
            inputs, outputs = [], []
            obj = self.obj._model.by_uuid(child.id)
            if isinstance(obj, cs.Component):
                self.update_children_size(child, exchanges)
                return

            port_ids = {p.id for p in child.ports}
            for ex in exchanges:
                source, target = ex.sources[0], ex.targets[0]
                if source in port_ids:
                    outputs.append(source)
                elif target in port_ids:
                    inputs.append(target)

            childnum = max(len(inputs), len(outputs))
            height = max(
                child.height + 2 * makers.LABEL_VPAD,
                makers.PORT_PADDING
                + (makers.PORT_SIZE + makers.PORT_PADDING) * childnum,
            )
            child.height = height
            stack_height += makers.NEIGHBOR_VMARGIN + height

        if stack_height > 0:
            data.height = stack_height

    @abc.abstractmethod
    def collect(self) -> None:
        """Populate the elkdata container."""
        raise NotImplementedError


def get_elkdata_for_exchanges(
    diagram: context.InterfaceContextDiagram
    | context.FunctionalContextDiagram,
    collector_type: type[ExchangeCollector],
    params: dict[str, t.Any],
) -> _elkjs.ELKInputData:
    """Return exchange data for ELK."""
    data = makers.make_diagram(diagram)
    data.layoutOptions["layered.nodePlacement.strategy"] = "NETWORK_SIMPLEX"
    collector = collector_type(diagram, data, params)
    collector.collect()
    for comp in data.children:
        collector.update_children_size(comp, data.edges)
    return data


class InterfaceContextCollector(ExchangeCollector):
    """Collect context data for interfaces.

    Collect necessary
    [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
    for building the interface context.
    """

    left: _elkjs.ELKInputChild | None
    """Left (source) Component Box of the interface."""
    right: _elkjs.ELKInputChild | None
    """Right (target) Component Box of the interface."""
    outgoing_edges: dict[str, m.ModelElement]
    incoming_edges: dict[str, m.ModelElement]

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        self.left: _elkjs.ELKInputChild | None = None
        self.right: _elkjs.ELKInputChild | None = None
        self.incoming_edges = {}
        self.outgoing_edges = {}

        super().__init__(diagram, data, params)

    def get_left_and_right(self) -> None:
        try:
            self.collect_context()

            port_spread = len(self.outgoing_edges) - len(self.incoming_edges)
            _port_spread = len(self.incoming_edges) - len(self.outgoing_edges)
            if port_spread < _port_spread:
                self.incoming_edges, self.outgoing_edges = (
                    self.outgoing_edges,
                    self.incoming_edges,
                )
                self.left, self.right = self.right, self.left

            assert self.left is not None
            self.data.children.append(self.left)
            assert self.right is not None
            self.data.children.append(self.right)
            if self.left == self.right:
                raise errors.CycleError(
                    "The interface is a cycle, connecting the same "
                    "source and target."
                )

        except AttributeError as error:
            logger.exception("Interface collection failed: \n%r", str(error))

    def collect_context(self):
        self.left = makers.make_box(self.get_source(self.obj), no_symbol=True)
        self.right = makers.make_box(self.get_target(self.obj), no_symbol=True)
        boxes: dict[str, _elkjs.ELKInputChild] = {
            self.left.id: self.left,
            self.right.id: self.right,
        }
        for fex in self.get_alloc_fex(self.obj):
            try:
                src_id = self.make_all_owners(fex.source, boxes)
            except ValueError as error:
                logger.debug("%s", error)
                continue

            try:
                trg_id = self.make_all_owners(fex.target, boxes)
            except ValueError as error:
                src_port = boxes[fex.source.owner.uuid].ports[-1]
                if src_port.id == fex.source.uuid:
                    boxes[fex.source.owner.uuid].ports.remove(src_port)
                    logger.debug("%s", error)

                continue

            if [src_id, trg_id] == [self.right.id, self.left.id]:
                self.incoming_edges[fex.uuid] = fex
            elif [src_id, trg_id] == [self.left.id, self.right.id]:
                self.outgoing_edges[fex.uuid] = fex

        for uuid, box in boxes.items():
            element = self.obj._model.by_uuid(uuid)
            if isinstance(element, fa.AbstractFunction) and (
                parent_box := boxes.get(element.parent.uuid)
            ):
                owner_box = boxes[element.owner.uuid]
                owner_box.children.remove(box)
                parent_box.children.append(box)
                for label in parent_box.labels:
                    label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS

        if self.left.children:
            for label in self.left.labels:
                label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
        if self.right.children:
            for label in self.left.labels:
                label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS

    def make_all_owners(
        self,
        obj: fa.AbstractFunction | fa.FunctionPort,
        boxes: dict[str, _elkjs.ELKInputChild],
    ) -> str:
        owners: list[m.ModelElement] = []
        assert self.right is not None
        assert self.left is not None
        root: _elkjs.ELKInputChild | None = None
        for uuid in generic.get_all_owners(obj):
            element = self.obj._model.by_uuid(uuid)
            if uuid in {self.right.id, self.left.id}:
                root = boxes[uuid]
                break

            owners.append(element)

        if root is None:
            raise ValueError(f"No root found for {obj._short_repr_()}")

        owner_box: _elkjs.ELKInputChild = root
        for owner in reversed(owners):
            if isinstance(owner, fa.FunctionPort):
                if owner.uuid in (p.id for p in owner_box.ports):
                    continue

                owner_box.ports.append(makers.make_port(owner.uuid))
            else:
                if owner.uuid in (b.id for b in owner_box.children):
                    owner_box = boxes[owner.uuid]
                    continue

                box = boxes.setdefault(
                    owner.uuid, makers.make_box(owner, no_symbol=True)
                )
                owner_box.children.append(box)
                for label in owner_box.labels:
                    label.layoutOptions = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
                owner_box = box

        return root.id

    def add_interface(self) -> None:
        """Add the ComponentExchange (interface) to the collected data."""
        ex_data = generic.ExchangeData(
            self.obj,
            self.data,
            self.diagram.filters,
            self.params,
            is_hierarchical=False,
        )
        src, tgt = generic.exchange_data_collector(ex_data)
        self.data.edges[-1].layoutOptions = copy.deepcopy(
            _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
        )
        assert self.right is not None
        assert self.left is not None
        self.left.ports.append(makers.make_port(src.uuid))
        self.right.ports.append(makers.make_port(tgt.uuid))

    def collect(self) -> None:
        """Collect all allocated `FunctionalExchange`s in the context."""
        self.get_left_and_right()
        if self.diagram._hide_functions:
            assert self.left is not None
            self.left.children = []
            assert self.right is not None
            self.right.children = []
            self.incoming_edges = {}
            self.outgoing_edges = {}

        if self.diagram._include_interface or self.diagram._hide_functions:
            self.add_interface()

        try:
            for ex in (self.incoming_edges | self.outgoing_edges).values():
                ex_data = generic.ExchangeData(
                    ex,
                    self.data,
                    self.diagram.filters,
                    self.params,
                    is_hierarchical=False,
                )
                src, tgt = generic.exchange_data_collector(ex_data)
                if ex in self.incoming_edges.values():
                    self.data.edges[-1].sources = [tgt.uuid]
                    self.data.edges[-1].targets = [src.uuid]

            if not self.data.edges:
                logger.warning(
                    "There are no FunctionalExchanges allocated to '%s'.",
                    self.obj.name,
                )
        except AttributeError:
            pass


class PhysicalLinkContextCollector(ExchangeCollector):
    """Collects a `PhysicalLink` context.

    Collect necessary
    [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
    for building the ``PhysicalLink`` context.
    """

    left: _elkjs.ELKInputChild | None
    """Left partner of the interface."""
    right: _elkjs.ELKInputChild | None
    """Right partner of the interface."""

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        self.left: _elkjs.ELKInputChild | None = None
        self.right: _elkjs.ELKInputChild | None = None

        super().__init__(diagram, data, params)

    def get_owner_savely(self, attr_getter: t.Callable) -> m.ModelElement:
        try:
            return (owner := attr_getter(self.obj))
        except RuntimeError as error:
            # pylint: disable-next=raise-missing-from
            raise errors.CapellambseError(
                f"Failed to collect source of '{self.obj.name}'"
            ) from error
        except AttributeError as error:
            assert owner is None
            # pylint: disable-next=raise-missing-from
            raise errors.CapellambseError(
                f"Port has no owner: '{self.obj.name}'"
            ) from error

    def get_left_and_right(self) -> None:
        source = self.get_owner_savely(self.get_source)
        target = self.get_owner_savely(self.get_target)
        self.left = makers.make_box(source, no_symbol=True)
        self.right = makers.make_box(target, no_symbol=True)
        self.data.children.extend([self.left, self.right])

    def add_interface(self) -> None:
        """Add the ComponentExchange (interface) to the collected data."""
        ex_data = generic.ExchangeData(
            self.obj,
            self.data,
            self.diagram.filters,
            self.params,
            is_hierarchical=False,
        )
        src, tgt = generic.exchange_data_collector(ex_data)
        self.data.edges[-1].layoutOptions = copy.deepcopy(
            _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS
        )
        assert self.right is not None
        assert self.left is not None
        left_port, right_port = self.get_source_and_target_ports(src, tgt)
        self.left.ports.append(left_port)
        self.right.ports.append(right_port)

    def get_source_and_target_ports(
        self, src: m.ModelElement, tgt: m.ModelElement
    ) -> tuple[_elkjs.ELKInputPort, _elkjs.ELKInputPort]:
        """Return the source and target ports of the interface."""
        left_port = makers.make_port(src.uuid)
        right_port = makers.make_port(tgt.uuid)
        if self.diagram._display_port_labels:
            left_port.labels = makers.make_label(src.name)
            right_port.labels = makers.make_label(tgt.name)

            _plp = self.diagram._port_label_position
            if not (plp := getattr(_elkjs.PORT_LABEL_POSITION, _plp, None)):
                raise ValueError(f"Invalid port label position '{_plp}'.")

            assert isinstance(plp, _elkjs.PORT_LABEL_POSITION)
            port_label_position = plp.name

            assert self.left is not None
            self.left.layoutOptions["portLabels.placement"] = (
                port_label_position
            )
            assert self.right is not None
            self.right.layoutOptions["portLabels.placement"] = (
                port_label_position
            )
        return left_port, right_port

    def collect(self) -> None:
        """Collect all allocated `PhysicalLink`s in the context."""
        self.get_left_and_right()
        if self.diagram._include_interface:
            self.add_interface()


class FunctionalContextCollector(ExchangeCollector):
    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        super().__init__(diagram, data, params)

    def collect(self) -> None:
        raise NotImplementedError()


def is_hierarchical(
    ex: m.ModelElement,
    box: _elkjs.ELKInputChild,
    key: t.Literal["ports"] | t.Literal["children"] = "ports",
) -> bool:
    """Check if the exchange is hierarchical (nested) inside ``box``."""
    src, trg = generic.collect_exchange_endpoints(ex)
    objs = {o.id for o in getattr(box, key)}
    attr_map = {"children": "parent.uuid", "ports": "parent.parent.uuid"}
    attr_getter = operator.attrgetter(attr_map[key])
    source_contained = src.uuid in objs or attr_getter(src) == box.id
    target_contained = trg.uuid in objs or attr_getter(trg) == box.id
    return source_contained and target_contained


def functional_context_collector(
    diagram: context.FunctionalContextDiagram, pars: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    return get_elkdata_for_exchanges(diagram, FunctionalContextCollector, pars)


def interface_context_collector(
    diagram: context.InterfaceContextDiagram, pars: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    collector: type[ExchangeCollector]
    if isinstance(diagram.target, cs.PhysicalLink):
        collector = PhysicalLinkContextCollector
    else:
        collector = InterfaceContextCollector

    return get_elkdata_for_exchanges(diagram, collector, pars)
