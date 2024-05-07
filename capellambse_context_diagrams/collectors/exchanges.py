# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import logging
import operator
import typing as t

from capellambse.model import common
from capellambse.model.crosslayer import cs
from capellambse.model.modeltypes import DiagramType as DT

from .. import _elkjs, context
from . import generic, makers

logger = logging.getLogger(__name__)


class ExchangeCollector(metaclass=abc.ABCMeta):
    """Base class for context collection on Exchanges."""

    intermap: dict[str, DT] = {
        DT.OAB: ("source", "target", "allocated_interactions", "activities"),
        DT.SAB: (
            "source.parent",
            "target.parent",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
        DT.LAB: (
            "source.parent",
            "target.parent",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
        DT.PAB: (
            "source.parent",
            "target.parent",
            "allocated_functional_exchanges",
            "allocated_functions",
        ),
    }

    def __init__(
        self,
        diagram: (
            context.InterfaceContextDiagram | context.FunctionalContextDiagram
        ),
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

    def get_functions_and_exchanges(
        self, comp: common.GenericElement, interface: common.GenericElement
    ) -> tuple[
        list[common.GenericElement],
        dict[str, common.GenericElement],
        dict[str, common.GenericElement],
    ]:
        """Return `Function`s, incoming and outgoing
        `FunctionalExchange`s for given `Component` and `interface`.
        """
        functions, incomings, outgoings = [], {}, {}
        alloc_functions = self.get_alloc_functions(comp)
        for fex in self.get_alloc_fex(interface):
            source = self.get_source(fex)
            if source in alloc_functions:
                if fex.uuid not in outgoings:
                    outgoings[fex.uuid] = fex
                if source not in functions:
                    functions.append(source)

            target = self.get_target(fex)
            if target in alloc_functions:
                if fex.uuid not in incomings:
                    incomings[fex.uuid] = fex
                if target not in functions:
                    functions.append(target)

        return functions, incomings, outgoings

    def collect_context(
        self, comp: common.GenericElement, interface: common.GenericElement
    ) -> tuple[
        dict[str, t.Any],
        dict[str, common.GenericElement],
        dict[str, common.GenericElement],
    ]:
        functions, incomings, outgoings = self.get_functions_and_exchanges(
            comp, interface
        )
        components = []
        for cmp in comp.components:
            fncs, _, _ = self.get_functions_and_exchanges(cmp, interface)
            functions.extend(fncs)
            if fncs:
                c, incs, outs = self.collect_context(cmp, interface)
                components.append(c)
                incomings |= incs
                outgoings |= outs
        return (
            {
                "element": comp,
                "functions": functions,
                "components": components,
            },
            incomings,
            outgoings,
        )

    def make_ports_and_update_children_size(
        self,
        data: _elkjs.ELKInputChild,
        exchanges: t.Sequence[_elkjs.ELKInputEdge],
    ) -> None:
        """Adjust size of functions and make ports."""
        stack_height: int | float = -makers.NEIGHBOR_VMARGIN
        for child in data["children"]:
            inputs, outputs = [], []
            obj = self.obj._model.by_uuid(child["id"])
            if isinstance(obj, cs.Component):
                self.make_ports_and_update_children_size(child, exchanges)
                return
            port_ids = {p.uuid for p in obj.inputs + obj.outputs}
            for ex in exchanges:
                source, target = ex["sources"][0], ex["targets"][0]
                if source in port_ids:
                    outputs.append(source)
                elif target in port_ids:
                    inputs.append(target)

            if generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[self.diagram.type]:
                child["ports"] = [
                    makers.make_port(i) for i in set(inputs + outputs)
                ]

            childnum = max(len(inputs), len(outputs))
            height = max(
                child["height"] + 2 * makers.LABEL_VPAD,
                makers.PORT_PADDING
                + (makers.PORT_SIZE + makers.PORT_PADDING) * childnum,
            )
            child["height"] = height
            stack_height += makers.NEIGHBOR_VMARGIN + height

        data["height"] = stack_height

    @abc.abstractmethod
    def collect(self) -> None:
        """Populate the elkdata container."""
        raise NotImplementedError


def get_elkdata_for_exchanges(
    diagram: (
        context.InterfaceContextDiagram | context.FunctionalContextDiagram
    ),
    collector_type: type[ExchangeCollector],
    params: dict[str, t.Any],
) -> _elkjs.ELKInputData:
    """Return exchange data for ELK."""
    data = makers.make_diagram(diagram)
    collector = collector_type(diagram, data, params)
    collector.collect()
    for comp in data["children"]:
        collector.make_ports_and_update_children_size(comp, data["edges"])

    return data


class InterfaceContextCollector(ExchangeCollector):
    """Collect necessary
    [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
    for building the interface context.
    """

    left: _elkjs.ELKInputChild | None
    """Left (source) Component Box of the interface."""
    right: _elkjs.ELKInputChild | None
    """Right (target) Component Box of the interface."""
    outgoing_edges: dict[str, common.GenericElement]
    incoming_edges: dict[str, common.GenericElement]

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        self.left = None
        self.right = None
        self.incoming_edges = {}
        self.outgoing_edges = {}

        super().__init__(diagram, data, params)

        self.get_left_and_right()
        if diagram.include_interface:
            self.add_interface()

    def get_left_and_right(self) -> None:
        made_children: set[str] = set()

        def get_capella_order(
            comp: common.GenericElement, functions: list[common.GenericElement]
        ) -> list[common.GenericElement]:
            alloc_functions = self.get_alloc_functions(comp)
            return [fnc for fnc in alloc_functions if fnc in functions]

        def make_boxes(cntxt: dict[str, t.Any]) -> _elkjs.ELKInputChild | None:
            comp = cntxt["element"]
            functions = cntxt["functions"]
            components = cntxt["components"]
            if comp.uuid not in made_children:
                children = [
                    makers.make_box(fnc)
                    for fnc in functions
                    if fnc in self.get_alloc_functions(comp)
                ]
                for cmp in components:
                    if child := make_boxes(cmp):
                        children.append(child)
                if children:
                    layout_options = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
                else:
                    layout_options = makers.CENTRIC_LABEL_LAYOUT_OPTIONS

                box = makers.make_box(
                    comp, no_symbol=True, layout_options=layout_options
                )
                box["children"] = children
                made_children.add(comp.uuid)
                return box
            return None

        try:
            comp = self.get_source(self.obj)
            left_context, incs, outs = self.collect_context(comp, self.obj)
            inc_port_ids = set(ex.target.uuid for ex in incs.values())
            out_port_ids = set(ex.source.uuid for ex in outs.values())
            port_spread = len(out_port_ids) - len(inc_port_ids)

            _comp = self.get_target(self.obj)
            right_context, _, _ = self.collect_context(_comp, self.obj)
            _inc_port_ids = set(ex.target.uuid for ex in outs.values())
            _out_port_ids = set(ex.source.uuid for ex in incs.values())
            _port_spread = len(_out_port_ids) - len(_inc_port_ids)

            left_context["functions"] = get_capella_order(
                comp, left_context["functions"]
            )
            right_context["functions"] = get_capella_order(
                _comp, right_context["functions"]
            )
            if port_spread >= _port_spread:
                self.incoming_edges = incs
                self.outgoing_edges = outs
            else:
                self.incoming_edges = outs
                self.outgoing_edges = incs
                left_context, right_context = right_context, left_context

            if left_child := make_boxes(left_context):
                self.data["children"].append(left_child)
                self.left = left_child
            if right_child := make_boxes(right_context):
                self.data["children"].append(right_child)
                self.right = right_child
        except AttributeError:
            pass

    def add_interface(self) -> None:
        ex_data = generic.ExchangeData(
            self.obj,
            self.data,
            self.diagram.filters,
            self.params,
            is_hierarchical=False,
        )
        src, tgt = generic.exchange_data_collector(ex_data)
        assert self.right is not None
        if self.get_source(self.obj).uuid == self.right["id"]:
            self.data["edges"][-1]["sources"] = [tgt.uuid]
            self.data["edges"][-1]["targets"] = [src.uuid]

        assert self.left is not None
        self.left.setdefault("ports", []).append(makers.make_port(src.uuid))
        self.right.setdefault("ports", []).append(makers.make_port(tgt.uuid))

    def collect(self) -> None:
        """Collect all allocated `FunctionalExchange`s in the context."""
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
                    self.data["edges"][-1]["sources"] = [tgt.uuid]
                    self.data["edges"][-1]["targets"] = [src.uuid]

            if not self.data["edges"]:
                logger.warning(
                    "There are no FunctionalExchanges allocated to '%s'.",
                    self.obj.name,
                )
        except AttributeError:
            pass


class FunctionalContextCollector(ExchangeCollector):
    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
        params: dict[str, t.Any],
    ) -> None:
        super().__init__(diagram, data, params)

    def collect(self) -> None:
        functional_exchanges: list[common.GenericElement] = []
        all_functions: list[common.GenericElement] = []
        made_children: set[str] = {self.obj.uuid}
        try:
            for interface in self.obj.exchanges:
                if self.get_source(interface) == self.obj:
                    comp = self.get_target(interface)
                else:
                    comp = self.get_source(interface)

                functions, inc, outs = self.get_functions_and_exchanges(
                    self.obj, interface
                )
                if comp.uuid not in made_children:
                    children = [makers.make_box(c) for c in functions]
                    if children:
                        layout_options = makers.DEFAULT_LABEL_LAYOUT_OPTIONS
                    else:
                        layout_options = makers.CENTRIC_LABEL_LAYOUT_OPTIONS

                    box = makers.make_box(comp, layout_options=layout_options)
                    box["children"] = children
                    self.data["children"].append(box)
                    made_children.add(comp.uuid)

                all_functions.extend(functions)
                functional_exchanges.extend(inc | outs)

            self.data["children"][0]["children"] = [
                makers.make_box(c)
                for c in all_functions
                if c in self.obj.functions
            ]
        except AttributeError:
            pass

        for ex in functional_exchanges:
            generic.exchange_data_collector(
                generic.ExchangeData(
                    ex, self.data, set(), is_hierarchical=False
                )
            )


def is_hierarchical(
    ex: common.GenericElement,
    box: _elkjs.ELKInputChild,
    key: t.Literal["ports"] | t.Literal["children"] = "ports",
) -> bool:
    """Check if the exchange is hierarchical (nested) inside ``box``."""
    src, trg = generic.collect_exchange_endpoints(ex)
    objs = {o["id"] for o in box[key]}
    attr_map = {"children": "parent.uuid", "ports": "parent.parent.uuid"}
    attr_getter = operator.attrgetter(attr_map[key])
    source_contained = src.uuid in objs or attr_getter(src) == box["id"]
    target_contained = trg.uuid in objs or attr_getter(trg) == box["id"]
    return source_contained and target_contained
