# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import collections.abc as cabc
import logging
import operator
import typing as t

from capellambse import helpers
from capellambse.model import common
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
        diagram: context.InterfaceContextDiagram
        | context.FunctionalContextDiagram,
        data: _elkjs.ELKInputData,
    ) -> None:
        self.diagram = diagram
        self.data: _elkjs.ELKInputData = data
        self.obj = self.diagram.target
        src, trg, alloc_fex, fncs = self.intermap[diagram.type]
        self.get_source = operator.attrgetter(src)
        self.get_target = operator.attrgetter(trg)
        self.get_alloc_fex = operator.attrgetter(alloc_fex)
        self.get_alloc_functions = operator.attrgetter(fncs)

    def get_functions_and_exchanges(
        self, comp: common.GenericElement, interface: common.GenericElement
    ) -> tuple[
        list[common.GenericElement],
        list[common.GenericElement],
        list[common.GenericElement],
    ]:
        """Return `Function`s, incoming and outgoing
        `FunctionalExchange`s for given `Component` and `interface`.
        """
        functions, outgoings, incomings = [], [], []
        alloc_functions = self.get_alloc_functions(comp)
        for fex in self.get_alloc_fex(interface):
            source = self.get_source(fex)
            if source in alloc_functions:
                if fex not in outgoings:
                    outgoings.append(fex)
                if source not in functions:
                    functions.append(source)

            target = self.get_target(fex)
            if target in alloc_functions:
                if fex not in incomings:
                    incomings.append(fex)
                if target not in functions:
                    functions.append(target)

        return functions, incomings, outgoings

    def make_ports_and_update_children_size(
        self,
        data: _elkjs.ELKInputChild,
        exchanges: t.Sequence[_elkjs.ELKInputEdge],
    ) -> None:
        """Adjust size of functions and make ports."""
        stack_height = -makers.NEIGHBOR_VMARGIN
        for child in data["children"]:
            inputs, outputs = [], []
            obj = self.obj._model.by_uuid(child["id"])
            for ex in exchanges:
                source, target = ex["sources"][0], ex["targets"][0]
                port_ids = [p.uuid for p in obj.inputs + obj.outputs]
                if source in port_ids:
                    outputs.append(source)
                elif target in port_ids:
                    inputs.append(target)

            if self.diagram.type not in generic.PORTLESS_DIAGRAM_TYPES:
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
    def collect(self) -> cabc.MutableSequence[_elkjs.ELKInputEdge]:
        return NotImplemented


def get_elkdata_for_exchanges(
    diagram: context.InterfaceContextDiagram
    | context.FunctionalContextDiagram,
    collector_type: type[ExchangeCollector],
) -> _elkjs.ELKInputData:
    """Return exchange data for ELK."""
    data = makers.make_diagram(diagram)
    collector = collector_type(diagram, data)
    data["edges"] = collector.collect()
    for comp in data["children"]:
        collector.make_ports_and_update_children_size(comp, data["edges"])

    return data


class InterfaceContextCollector(ExchangeCollector):
    """Collect necessary
    [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
    for building the interface context.
    """

    left: common.GenericElement
    """Source or target Component of the interface."""
    right: common.GenericElement
    """Source or target Component of the interface."""
    outgoing_edges: list[common.GenericElement]
    incoming_edges: list[common.GenericElement]

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        data: _elkjs.ELKInputData,
    ) -> None:
        super().__init__(diagram, data)
        self.get_left_and_right()

    def get_left_and_right(self) -> None:
        made_children: set[str] = set()

        def get_capella_order(
            comp: common.GenericElement, functions: list[common.GenericElement]
        ) -> list[common.GenericElement]:
            alloc_functions = self.get_alloc_functions(comp)
            return [fnc for fnc in alloc_functions if fnc in functions]

        def make_boxes(
            comp: common.GenericElement, functions: list[common.GenericElement]
        ) -> None:
            if comp.uuid not in made_children:
                box = makers.make_box(comp, no_symbol=True)
                box["children"] = [
                    makers.make_box(c)
                    for c in functions
                    if c in self.get_alloc_functions(comp)
                ]
                self.data["children"].append(box)
                made_children.add(comp.uuid)

        try:
            comp = self.get_source(self.obj)
            functions, incs, outs = self.get_functions_and_exchanges(
                comp, self.obj
            )
            inc_port_ids = set(ex.target.uuid for ex in incs)
            out_port_ids = set(ex.source.uuid for ex in outs)
            port_spread = len(out_port_ids) - len(inc_port_ids)

            _comp = self.get_target(self.obj)
            _functions, _, _ = self.get_functions_and_exchanges(
                _comp, self.obj
            )
            _inc_port_ids = set(ex.target.uuid for ex in outs)
            _out_port_ids = set(ex.source.uuid for ex in incs)
            _port_spread = len(_out_port_ids) - len(_inc_port_ids)
            functions = get_capella_order(comp, functions)
            _functions = get_capella_order(_comp, _functions)
            if port_spread >= _port_spread:
                self.left = comp
                self.right = _comp
                self.outgoing_edges = outs
                self.incoming_edges = incs
                left_functions = functions
                right_functions = _functions
            else:
                self.left = _comp
                self.right = comp
                self.outgoing_edges = incs
                self.incoming_edges = outs
                left_functions = _functions
                right_functions = functions

            make_boxes(self.left, left_functions)
            make_boxes(self.right, right_functions)
        except AttributeError:
            pass

    def collect(self) -> cabc.MutableSequence[_elkjs.ELKInputEdge]:
        """Return all allocated `FunctionalExchange`s in the context."""
        functional_exchanges: list[_elkjs.ELKInputEdge] = []
        try:
            for ex in self.incoming_edges + self.outgoing_edges:
                try:
                    src, tgt = generic.collect_exchange_endpoints(ex)
                except AttributeError:
                    continue

                width, height = helpers.extent_func(ex.name)
                swap = ex in self.incoming_edges
                functional_exchanges.append(
                    _elkjs.ELKInputEdge(
                        id=ex.uuid,
                        sources=[tgt.uuid] if swap else [src.uuid],
                        targets=[src.uuid] if swap else [tgt.uuid],
                        labels=[
                            _elkjs.ELKInputLabel(
                                text=ex.name,
                                width=width + 2 * makers.LABEL_HPAD,
                                height=height + 2 * makers.LABEL_VPAD,
                            )
                        ],
                    )
                )

            if not functional_exchanges:
                logger.warning(
                    "There are no FunctionalExchanges allocated to '%s'.",
                    self.obj.name,
                )
        except AttributeError:
            pass

        return functional_exchanges


class FunctionalContextCollector(ExchangeCollector):
    def collect(self) -> cabc.MutableSequence[_elkjs.ELKInputEdge]:
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
                    box = makers.make_box(comp)
                    box["children"] = [makers.make_box(c) for c in functions]
                    self.data["children"].append(box)
                    made_children.add(comp.uuid)

                all_functions.extend(functions)
                functional_exchanges.extend(inc + outs)

            self.data["children"][0]["children"] = [
                makers.make_box(c)
                for c in all_functions
                if c in self.obj.functions
            ]
        except AttributeError:
            pass

        for ex in functional_exchanges:
            generic.exchange_data_collector(
                generic.ExchangeData(ex, self.data, set())
            )

        return self.data["edges"]
