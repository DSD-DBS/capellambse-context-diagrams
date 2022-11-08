# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Data model needed for context collection."""
from __future__ import annotations

import collections.abc as cabc
import dataclasses
import itertools
import logging
import operator
import typing as t

import capellambse
from capellambse.model import common

logger = logging.getLogger(__name__)

ModelQuery = cabc.Callable[
    [common.ModelObject], t.Union[common.ModelObject, common.ElementList]
]
EndpointsQuery = tuple[ModelQuery, ModelQuery]


class InvalidContextDescription(Exception):
    """Raised when context description is faulty."""


@dataclasses.dataclass
class TargetDescription:
    """A description of a target for an exchange."""

    types: cabc.Sequence[type[common.ModelObject]]

    queries: tuple[str, str] = dataclasses.field(
        default_factory=lambda: ("source", "target")
    )
    targets: cabc.Sequence[TargetDescription] = dataclasses.field(
        default_factory=lambda: []
    )

    @property
    def end_types(self) -> set[type[common.ModelObject]]:
        """Return terminal types of the ``TargetDescription`` chain."""
        if self.targets:
            end_types = (target.end_types for target in self.targets)
            return set(itertools.chain.from_iterable(end_types))
        return set(self.types)

    @property
    def full_queries(self) -> list[tuple[str, str]]:
        """Return a sequence of queries in order to receive the target."""
        full_target_queries = itertools.chain.from_iterable(
            target.full_queries for target in self.targets
        )
        return [self.queries] + list(full_target_queries)

    @classmethod
    def from_dict(
        cls, description: cabc.Mapping[str, t.Any]
    ) -> TargetDescription:
        """Return a ``TargetDescription`` from a given dictionary."""
        types = description.get("types", [])
        if not types:
            types = list(description.keys())
            if len(types) > 1:
                raise InvalidContextDescription(
                    f"Invalid 'targets' description format: '{description!r}'."
                    " Either use 'types' key for listing multiple target types"
                    " collected via the same queries (and targets) or single"
                    " key for a target type with individual queries (and"
                    " targets)."
                )

            description = description[types[0]]

        optional_params = dict[str, t.Any]()
        if queries := description.get("queries", []):
            try:
                source_query, target_query = queries
            except ValueError as err:
                raise InvalidContextDescription(
                    "Invalid number of 'queries' in target description:"
                    f" '{queries!r}'. Only 2 queries (for source and target)"
                    "are valid."
                ) from err

            optional_params["queries"] = (source_query, target_query)
        if targets := description.get("targets", []):
            optional_params["targets"] = _get_target_descriptions(targets)

        return TargetDescription(
            [_get_type(type) for type in types], **optional_params
        )


def _get_target_descriptions(
    targets: cabc.Iterable[str | cabc.Mapping[str, t.Any]],
) -> list[TargetDescription]:
    r"""Return a list of ``TargetDescription`` \s from given ``targets``."""
    return [
        TargetDescription([_get_type(target)])
        if isinstance(target, str)
        else TargetDescription.from_dict(target)
        for target in targets
    ]


def _get_type(target_type: str) -> type[common.ModelObject]:
    try:
        return next(_match_from_xtype_handlers(target_type))
    except StopIteration as err:
        raise InvalidContextDescription(
            f"Unknown 'type' in 'targets': {target_type!r}"
        ) from err


def _match_from_xtype_handlers(
    target_type: str,
) -> cabc.Iterator[type[common.ModelObject]]:
    for handlers in common.XTYPE_HANDLERS.values():
        for xtype, ctype in handlers.items():
            handle_type = xtype.split(":")[-1]
            if handle_type == target_type:
                yield ctype


@dataclasses.dataclass
class ExchangeDescription:
    """A description of an exchange to be collected in the context."""

    model: dataclasses.InitVar[capellambse.MelodyModel]
    subject: dataclasses.InitVar[str]
    targets: cabc.Sequence[TargetDescription]
    types: set[str]

    candidates: set[common.ModelObject] = dataclasses.field(init=False)
    direction: str = "bi"
    source_end_types: tuple[type[common.ModelObject], ...] = dataclasses.field(
        init=False
    )
    target_end_types: tuple[type[common.ModelObject], ...] = dataclasses.field(
        init=False
    )
    target_queries: cabc.Mapping[
        type[common.ModelObject], cabc.Sequence[EndpointsQuery]
    ] = dataclasses.field(init=False)

    def __post_init__(
        self, model: capellambse.MelodyModel, subject: str
    ) -> None:
        if not self.types:
            raise InvalidContextDescription(
                "Invalid 'exchanges' in description: List of 'types' required"
            )

        if not self.targets:
            raise InvalidContextDescription(
                "Invalid 'exchanges' in description: List of 'targets' required"
            )

        self.candidates = set(model.search(*self.types))
        if not self.candidates:
            logger.warning(
                "No exchanges found in model with types: %r", self.types
            )

        end_types = self._get_end_types()
        if self.direction == "input":
            self.source_end_types = end_types
            self.target_end_types = (_get_type(subject),)
        elif self.direction == "output":
            self.source_end_types = (_get_type(subject),)
            self.target_end_types = end_types
        else:
            self.source_end_types = self.target_end_types = end_types

        self.target_queries = self._get_target_queries()

    @classmethod
    def from_dict(
        cls,
        exchange: dict[str, t.Any],
        model: capellambse.MelodyModel,
        subject: str,
    ) -> ExchangeDescription:
        """Return an ``ExchangeDescription`` from a given dictionary."""
        targets = _get_target_descriptions(exchange.get("targets", []))
        return cls(
            model=model,
            subject=subject,
            targets=targets,
            types=set(exchange.get("types", set())),
            direction=exchange.get("direction", "bi"),
        )

    def _get_end_types(self) -> tuple[type[common.ModelObject], ...]:
        types = set[type]()
        for target in self.targets:
            types |= set(target.end_types)

        return tuple(types)

    def _get_target_queries(
        self,
    ) -> dict[type[common.ModelObject], list[EndpointsQuery]]:
        query_map = {}
        for target in self.targets:
            target_queries: list[EndpointsQuery] = [
                (
                    operator.attrgetter(src_query),
                    operator.attrgetter(trg_query),
                )
                for src_query, trg_query in target.full_queries
            ]
            for ttype in set(target.types):
                query_map[ttype] = target_queries

        return query_map
