# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Build an ELK DataFlow diagram from collected capellambse context."""

from __future__ import annotations

import typing as t

import capellambse.model as m

from .. import _elkjs, _registry, context
from ..collectors import _generic, portless
from . import default

SUPPORTED_CLASSES: tuple[type[m.ModelElement], ...] = tuple(
    t[0] for t in _registry.DATAFLOW_CLASSES
)


class DiagramBuilder(default.DiagramBuilder):
    """Collect the data context for a DataFlow diagram."""

    def __init__(
        self,
        diagram: context.ContextDiagram,
        params: dict[str, t.Any],
    ) -> None:
        super().__init__(diagram, params)

        self.diagram_target_owners = []

    def _handle_boxeable_target(self) -> None:
        """Do nothing."""
        return

    def _get_data(self) -> _elkjs.ELKInputData:
        self.data.children = list(self.boxes.values())
        self.data.edges = list(self.edges.values())
        return self.data

    def _make_edge_and_ports(
        self,
        edge_obj: m.ModelElement,
        edge_data: default.EdgeData | None = None,
    ) -> _elkjs.ELKInputEdge | None:
        if self.edges.get(edge_obj.uuid):
            return None

        if edge_data is None:
            edge_data = self._collect_edge_data(edge_obj)

        return self._update_edge_common(edge_data)

    def _collect_edge_data(self, edge_obj: m.ModelElement) -> default.EdgeData:
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
        return default.EdgeData(
            edge_obj,
            edge,
            default.ConnectorData(src_obj, src_owner, True),
            default.ConnectorData(tgt_obj, tgt_owner, False),
        )


def builder(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    return default.builder(diagram, params, DiagramBuilder)
