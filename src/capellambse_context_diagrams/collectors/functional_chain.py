# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc as cabc
import typing as t

import capellambse.model as m
from capellambse.metamodel.fa import FunctionalChain

from .. import context

if t.TYPE_CHECKING:
    from .. import context


def collector(
    diagram: context.ContextDiagram,
) -> cabc.Iterator[m.ModelElement]:
    """Collect context data for a FunctionalChain."""
    if not isinstance(diagram.target, FunctionalChain):
        return

    functional_chain: FunctionalChain = diagram.target

    yield from functional_chain.involved
