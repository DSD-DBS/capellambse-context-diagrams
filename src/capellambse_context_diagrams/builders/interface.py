# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Build an ELK interface context from collected capellambse."""

from __future__ import annotations

import logging
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs

from .. import _elkjs, _registry, context, errors
from . import _makers, default

SUPPORTED_CLASSES: tuple[type[m.ModelElement], ...] = tuple(
    t[0] for t in _registry.INTERFACE_CONTEXT_CLASSES
)
logger = logging.getLogger(__name__)


class DiagramBuilder(default.DiagramBuilder):
    """Collect the data context for a DataFlow diagram."""

    def __init__(
        self,
        diagram: context.InterfaceContextDiagram,
        params: dict[str, t.Any],
    ):
        self.edge_data: dict[str, default.EdgeData] = {}
        self.incoming_edges: set[str] = set()
        self.outgoing_edges: set[str] = set()

        super().__init__(diagram, params)

        self.left: m.ModelElement = self.target.source
        self.right: m.ModelElement = self.target.target

    def _handle_boxeable_target(self) -> None:
        if self.left.owner == self.right.owner:
            raise errors.CycleError(
                "The interface is a cycle, connecting the same "
                "source and target."
            )

        if self.diagram._include_interface or self.diagram._hide_functions:
            self.data.layoutOptions["layered.nodePlacement.strategy"] = (
                "NETWORK_SIMPLEX"
            )
            edge = self._make_edge_and_ports(self.target)
            assert edge is not None
            edge.layoutOptions = (
                _elkjs.EDGE_STRAIGHTENING_LAYOUT_OPTIONS.copy()  # type: ignore[attr-defined]
            )

    def _make_edge_and_ports(
        self,
        edge_obj: m.ModelElement,
        edge_data: default.EdgeData | None = None,
    ) -> _elkjs.ELKInputEdge | None:
        if self.edges.get(edge_obj.uuid):
            return None

        if edge_data is None:
            edge_data = self._collect_edge_data(edge_obj)

        if edge_obj.uuid != self.target.uuid:
            owners = edge_data.source.owners + edge_data.target.owners
            if (
                self.left.owner.uuid not in owners
                or self.right.owner.uuid not in owners
            ) or self.diagram._hide_functions:
                return None

        self.edge_data[edge_obj.uuid] = edge_data
        return self._update_edge_common(edge_data)

    def _flip_edges(self) -> None:
        return None

    def _get_data(self) -> _elkjs.ELKInputData:
        super()._get_data()
        if self.diagram._hide_functions:
            assert self.left is not None
            left_box = next(
                (
                    c
                    for c in self.data.children
                    if c.id == self.left.owner.uuid
                ),
                None,
            )
            assert left_box is not None
            left_box.children = []
            assert self.right is not None
            right_box = next(
                (
                    c
                    for c in self.data.children
                    if c.id == self.right.owner.uuid
                ),
                None,
            )
            assert right_box is not None
            right_box.children = []

            for label in left_box.labels:
                label.layoutOptions = _makers.CENTRIC_LABEL_LAYOUT_OPTIONS

            for label in right_box.labels:
                label.layoutOptions = _makers.CENTRIC_LABEL_LAYOUT_OPTIONS

        for edge in self.data.edges:
            if edge.id == self.target.uuid:
                continue

            if edge.id in self.incoming_edges:
                edge.sources, edge.targets = edge.targets, edge.sources

        if not self.data.edges:
            logger.warning(
                "There is no context for %r.", self.target._short_repr_()
            )
        return self.data

    def __call__(self) -> _elkjs.ELKInputData:
        super().__call__()
        if len(self.data.children) > 2:
            for child in self.data.children[2:]:
                child_obj = self.target._model.by_uuid(child.id)
                if not isinstance(child_obj, cs.Component):
                    logger.warning(
                        "Non interface partner %r on lowest level. "
                        "Make sure to allocate all functions.",
                        child_obj._short_repr_(),
                    )

        if len(self.data.edges) < 2:
            return self._get_data()

        for edge in self.data.edges:
            if edge.id == self.target.uuid:
                continue

            edge_data = self.edge_data[edge.id]
            if self.left.owner.uuid in edge_data.source.owners:
                self.outgoing_edges.add(edge.id)
            elif (
                self.right.owner.uuid in edge_data.target.owners
                or self.left.owner.uuid in edge_data.target.owners
            ):
                self.incoming_edges.add(edge.id)
            elif self.right.owner.uuid in edge_data.source.owners:
                self.outgoing_edges.add(edge.id)

        to_right = len(self.outgoing_edges) - len(self.incoming_edges)
        to_left = len(self.incoming_edges) - len(self.outgoing_edges)
        if to_right < to_left:
            assert self.right is not None
            self.data.edges[0].sources = [self.right.uuid]
            assert self.left is not None
            self.data.edges[0].targets = [self.left.uuid]
            self.incoming_edges, self.outgoing_edges = (
                self.outgoing_edges,
                self.incoming_edges,
            )
        return self._get_data()


def builder(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    return default.builder(diagram, params, DiagramBuilder)
