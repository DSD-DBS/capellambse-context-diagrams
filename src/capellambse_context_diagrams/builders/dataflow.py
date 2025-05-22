# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Build an ELK DataFlow diagram from collected capellambse context."""

from __future__ import annotations

import typing as t

import capellambse.model as m

from .. import _elkjs, _registry, context
from . import _makers, default

SUPPORTED_CLASSES: tuple[type[m.ModelElement], ...] = tuple(
    t[0] for t in _registry.DATAFLOW_CLASSES
)


class DiagramBuilder(default.DiagramBuilder):
    """Collect the data context for a DataFlow diagram."""

    def _handle_boxeable_target(self) -> None:
        """Do nothing."""
        return

    def _get_data(self) -> _elkjs.ELKInputData:
        self.data.children = list(self.boxes.values())
        self.data.edges = list(self.edges.values())
        return self.data

    def _update_min_heights(
        self,
        uuid: str,
        side: str,
        port: _elkjs.ELKInputPort | None = None,
    ) -> None:
        if port is None:
            port = _makers.make_port("fake")
        return super()._update_min_heights(uuid, side, port)

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


def builder(
    diagram: context.ContextDiagram, params: dict[str, t.Any]
) -> _elkjs.ELKInputData:
    return default.builder(diagram, params, DiagramBuilder)
