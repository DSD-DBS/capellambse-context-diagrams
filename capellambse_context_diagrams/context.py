# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""
Definitions of Custom Accessor- and Diagram-Classtypes based on
[`Accessor`][capellambse.model.common.accessors.Accessor] and [`AbstractDiagram`][capellambse.model.diagram.AbstractDiagram].
"""
from __future__ import annotations

import collections.abc as cabc
import json
import logging
import typing as t

from capellambse import aird
from capellambse.model import common, diagram, modeltypes

from . import _elkjs, filters, serializers, styling
from .collectors import exchanges, get_elkdata

logger = logging.getLogger(__name__)


class ContextAccessor(common.Accessor):
    """Provides access to the context diagrams."""

    def __init__(self, dgcls: str) -> None:
        self._dgcls = dgcls

    @t.overload
    def __get__(self, obj: None, objtype=None) -> common.Accessor:
        ...

    @t.overload
    def __get__(
        self,
        obj: common.T,
        objtype: type[common.T] | None = None,
    ) -> ContextDiagram:
        ...

    def __get__(
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(obj, ContextDiagram)

    def _get(
        self,
        obj: common.GenericElement,
        diagram_class: type[ContextDiagram],
        diagram_id: str = "{}_context",
    ) -> common.Accessor | ContextDiagram:
        try:
            cache = getattr(
                obj._model, ".".join((__name__, diagram_class.__qualname__))
            )
        except AttributeError:
            cache = {}
            setattr(
                obj._model,
                ".".join((__name__, diagram_class.__qualname__)),
                cache,
            )
        diagram_id = diagram_id.format(obj.uuid)
        try:
            return cache[diagram_id]
        except KeyError:
            pass

        new_diagram = diagram_class(self._dgcls, obj)
        new_diagram.filters.add(filters.NO_UUID)
        cache[diagram_id] = new_diagram
        return new_diagram


class InterfaceContextAccessor(ContextAccessor):
    """Provides access to the interface context diagrams."""

    def __init__(  # pylint: disable=super-init-not-called
        self,
        diagclass: dict[type[common.GenericElement], str],
    ) -> None:
        self.__dgclasses = diagclass

    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        assert isinstance(obj.parent, common.GenericElement)
        self._dgcls = self.__dgclasses[obj.parent.__class__]
        return self._get(obj, InterfaceContextDiagram, "{}_interface_context")


class FunctionalContextAccessor(ContextAccessor):
    def __get__(  # type: ignore
        self,
        obj: common.T | None,
        objtype: type | None = None,
    ) -> common.Accessor | ContextDiagram:
        """Make a ContextDiagram for the given model object."""
        del objtype
        if obj is None:  # pragma: no cover
            return self
        assert isinstance(obj, common.GenericElement)
        return self._get(
            obj, FunctionalContextDiagram, "{}_functional_context"
        )


class ContextDiagram(diagram.AbstractDiagram):
    """An automatically generated context diagram.

    Attributes
    ----------
    target
        The `common.GenericElement` from which the context is collected
        from.
    styleclass
        The diagram class (for e.g. [LAB]).
    render_styles
        Dictionary with the `ElkChildType` in str format as keys and
        `styling.Styler` functions as values. An exanple is given by:
        [`styling.BLUE_ACTOR_FNCS`][capellambse_context_diagrams.styling.BLUE_ACTOR_FNCS]
    display_symbols_as_boxes
        Display objects that are normally displayed as symbol as a
        simple box instead, with the symbol being the box' icon. This
        avoids the object of interest to become one giant, oversized
        symbol in the middle of the diagram, and instead keeps the
        symbol small and only enlarges the surrounding box.
    serializer
        The serializer builds an `aird.Diagram` via
        [`serializers.DiagramSerializer.make_diagram`][capellambse_context_diagrams.serializers.DiagramSerializer.make_diagram]
        by converting every
        [`_elkjs.ELKOutputChild`][capellambse_context_diagrams._elkjs.ELKOutputChild]
        into an `aird.Box`, `aird.Edge` or `aird.Circle`.
    filters
        A list of filter names that are applied during collection of
        context. Currently this is only done in
        [`collectors.exchange_data_collector`][capellambse_context_diagrams.collectors.generic.exchange_data_collector].
    """

    def __init__(
        self,
        class_: str,
        obj: common.GenericElement,
        *,
        render_styles: dict[str, styling.Styler] | None = None,
        display_symbols_as_boxes: bool = False,
    ) -> None:
        super().__init__(obj._model)
        self.target = obj
        self.styleclass = class_

        self.render_styles = render_styles or styling.BLUE_ACTOR_FNCS
        self.serializer = serializers.DiagramSerializer(self)
        self.__filters: cabc.MutableSet[str] = self.FilterSet(self)
        self.display_symbols_as_boxes = display_symbols_as_boxes

    @property
    def uuid(self) -> str:  # type: ignore
        """Returns diagram UUID."""
        return f"{self.target.uuid}_context"

    @property
    def name(self) -> str:  # type: ignore
        """Returns the diagram name."""
        return f"Context of {self.target.name}"

    @property
    def type(self) -> modeltypes.DiagramType:
        """Return the type of this diagram."""
        try:
            return modeltypes.DiagramType(self.styleclass)
        except ValueError:  # pragma: no cover
            logger.warning("Unknown diagram type %r", self.styleclass)
            return modeltypes.DiagramType.UNKNOWN

    @property
    def nodes(self) -> common.MixedElementList:
        """Return a list of all nodes visible in this diagram."""
        adiagram = self.render(None)
        assert isinstance(adiagram, aird.Diagram)
        allids = {e.uuid for e in iter(adiagram)}
        assert None not in allids
        elems = []
        for elemid in allids:
            assert elemid is not None
            try:
                elem = self._model._loader[elemid]
            except (KeyError, StopIteration):  # pragma: no cover
                continue
            else:
                # Filter out visual-only elements that live in the
                # .aird / .airdfragment files
                frag = self._model._loader.find_fragment(elem)
                if frag.suffix not in {".aird", ".airdfragment"}:
                    elems.append(elem)

        return common.MixedElementList(
            self._model, elems, common.GenericElement
        )

    class FilterSet(cabc.MutableSet):
        """A set that stores filter_names and invalidates diagram cache."""

        def __init__(
            self,
            diagram: diagram.AbstractDiagram,  # pylint: disable=redefined-outer-name
        ) -> None:
            self._set: set[str] = set()
            self._diagram = diagram

        def add(self, value: str) -> None:
            if value not in filters.FILTER_LABEL_ADJUSTERS:
                logger.error("The filter '%s' is not yet supported.", value)
                return
            if value not in self._set:
                self._set.add(value)
                self._diagram.invalidate_cache()

        def discard(self, value: str) -> None:
            if value in self._set:
                self._diagram.invalidate_cache()
            return self._set.discard(value)

        def __contains__(self, x: object) -> bool:
            return self._set.__contains__(x)

        def __iter__(self) -> cabc.Iterator[str]:
            return self._set.__iter__()

        def __len__(self) -> int:
            return self._set.__len__()

    def _create_diagram(
        self,
        params: dict[str, t.Any],
        elkdata: _elkjs.ELKInputData | None = None,
    ) -> aird.Diagram:
        try:
            data = elkdata or get_elkdata(self, params)
            layout = _elkjs.call_elkjs(data)
        except json.JSONDecodeError as error:
            logger.error(json.dumps(data, indent=4))
            raise error
        return self.serializer.make_diagram(layout)

    @property  # type: ignore
    def filters(self) -> cabc.MutableSet[str]:  # type: ignore
        return self.__filters

    @filters.setter
    def filters(self, value: cabc.Iterable[str]) -> None:
        self.__filters.clear()
        self.__filters |= set(value)


class InterfaceContextDiagram(ContextDiagram):
    """An automatically generated Context Diagram exclusively for
    ``ComponentExchange``s.
    """

    def __init__(self, class_: str, obj: common.GenericElement, **kw) -> None:
        super().__init__(class_, obj, **kw, display_symbols_as_boxes=True)

    @property
    def name(self) -> str:  # type: ignore
        return f"Interface Context of {self.target.name}"

    def _create_diagram(
        self,
        params: dict[str, t.Any],
        elkdata: _elkjs.ELKInputData | None = None,
    ) -> aird.Diagram:
        return super()._create_diagram(
            params,
            elkdata
            or exchanges.get_elkdata_for_exchanges(
                self, exchanges.InterfaceContextCollector
            ),
        )


class FunctionalContextDiagram(ContextDiagram):
    """An automatically generated Context Diagram exclusively for
    Components.
    """

    @property
    def name(self) -> str:  # type: ignore
        return f"Interface Context of {self.target.name}"

    def _create_diagram(
        self,
        params: dict[str, t.Any],
        elkdata: _elkjs.ELKInputData | None = None,
    ) -> aird.Diagram:
        return super()._create_diagram(
            params,
            elkdata
            or exchanges.get_elkdata_for_exchanges(
                self, exchanges.FunctionalContextCollector
            ),
        )
