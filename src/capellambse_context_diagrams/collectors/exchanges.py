# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc as cabc
import operator

import capellambse.model as m
from capellambse.metamodel import cs
from capellambse.model import DiagramType as DT

from .. import context


def interface_context_collector(
    diagram: context.InterfaceContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Return the elements of the InterfaceContextDiagram."""
    if (
        not isinstance(diagram.target, cs.PhysicalLink)
        and not diagram._hide_functions
    ):
        intermap: dict[DT, tuple[str, str, str, str]] = {
            DT.OAB: (
                "source",
                "target",
                "allocated_interactions",
                "activities",
            ),
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
        _, _, alloc_fex, _ = intermap[diagram.type]
        get_alloc_fex = operator.attrgetter(alloc_fex)

        yield from get_alloc_fex(diagram.target)
