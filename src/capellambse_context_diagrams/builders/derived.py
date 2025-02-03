# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc as cabc
import typing as t

import capellambse.model as m
from capellambse.metamodel import cs, fa, la, sa

from .. import _elkjs, context
from ..collectors import _generic
from . import _makers

if t.TYPE_CHECKING:
    DerivatorFunction: t.TypeAlias = cabc.Callable[
        [
            context.ContextDiagram,
            dict[str, _elkjs.ELKInputChild],
            dict[str, _elkjs.ELKInputEdge],
        ],
        None,
    ]

    Filter: t.TypeAlias = cabc.Callable[
        [cabc.Iterable[m.ModelElement]],
        cabc.Iterable[m.ModelElement],
    ]


def derive_from_functions(
    diagram: context.ContextDiagram,
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
        inc, out = _generic.port_collector(fnc, diagram.type)
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
        box = _makers.make_box(
            derived_component,
            no_symbol=diagram._display_symbols_as_boxes,
        )
        class_ = diagram.serializer.get_styleclass(derived_component.uuid)
        box.id = f"{_makers.STYLECLASS_PREFIX}-{class_}:{uuid}"
        boxes[uuid] = box
        source_id = f"{_makers.STYLECLASS_PREFIX}-CP_INOUT:{i}"
        target_id = f"{_makers.STYLECLASS_PREFIX}-CP_INOUT:{-i}"
        box.ports.append(_makers.make_port(source_id))
        centerbox.ports.append(_makers.make_port(target_id))
        if i % 2 == 0:
            source_id, target_id = target_id, source_id

        uid = f"{_makers.STYLECLASS_PREFIX}-ComponentExchange:{i}"
        edges[uid] = _elkjs.ELKInputEdge(
            id=uid,
            sources=[source_id],
            targets=[target_id],
        )

    centerbox.height += (
        _makers.PORT_PADDING
        + (_makers.PORT_SIZE + _makers.PORT_PADDING) * i // 2
    )


DERIVATORS: dict[type[m.ModelElement], DerivatorFunction] = {
    la.LogicalComponent: derive_from_functions,
    sa.SystemComponent: derive_from_functions,
}
"""Supported objects to build derived contexts for."""
