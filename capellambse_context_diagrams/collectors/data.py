# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Data model needed for context collection."""
from __future__ import annotations

import collections.abc as cabc
import dataclasses
import itertools
import typing as t

import capellambse
from capellambse.model import common


class InvalidContextDescription(Exception):
    """Raised when context description is faulty."""


@dataclasses.dataclass
class TargetDescription:
    """A description of a target for an exchange."""

    types: cabc.Sequence[type[common.ModelObject]]

    queries: t.Optional[cabc.Sequence[str]] = dataclasses.field(
        default_factory=lambda: ["source", "target"]
    )
    targets: t.Optional[cabc.Sequence[TargetDescription]] = dataclasses.field(
        default_factory=lambda: []
    )

    @property
    def end_types(self) -> set[type[common.ModelObject]]:
        if self.targets:
            end_types = (target.end_types for target in self.targets)
            return set(itertools.chain.from_iterable(end_types))
        return set(self.types)

    @classmethod
    def from_dict(
        cls, description: cabc.Mapping[str, t.Any]
    ) -> TargetDescription:
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

        optional_params = {}
        if queries := description.get("queries", []):
            optional_params["queries"] = queries
        if targets := description.get("targets", []):
            optional_params["targets"] = get_target_descriptions(targets)

        return TargetDescription(
            [_get_type(type) for type in types], **optional_params
        )


def get_target_descriptions(
    targets: cabc.Iterable[str | cabc.Mapping[str, t.Any]],
) -> list[TargetDescription]:
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
    """A description of an exchange in the context."""

    targets: cabc.Sequence[TargetDescription]
    types: cabc.Sequence[str]
    model: dataclasses.InitVar[capellambse.MelodyModel]

    candidates: set[common.ModelObject] = dataclasses.field(init=False)
    direction: str = "bi"
    target_types: set[type[common.ModelObject]] = dataclasses.field(init=False)

    def __post_init__(self, model: capellambse.MelodyModel) -> None:
        self.candidates = set(model.search(*self.types))
        self.target_types = set()
        for target in self.targets:
            self.target_types |= set(target.end_types)
