# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Basic endpoint for the general collector of a ContextDiagram.

Functionality for collection of model data from an instance of
[`MelodyModel`][capellambse.model.MelodyModel] and conversion of it into
[`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData].
"""

from __future__ import annotations

import logging
import typing as t

from .. import _elkjs, context
from . import default, generic, portless

__all__ = ["get_elkdata"]
logger = logging.getLogger(__name__)


def get_elkdata(
    diagram: context.ContextDiagram, params: dict[str, t.Any] | None = None
) -> _elkjs.ELKInputData:
    """High level collector function to collect needed data for ELK.

    Parameters
    ----------
    diagram
        The [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram]
        instance to get the
        [`_elkjs.ELKInputData`][capellambse_context_diagrams._elkjs.ELKInputData]
        for.
    params
        Optional render params dictionary.

    Returns
    -------
    elkdata
        The data that can be fed into elkjs.
    """
    try:
        if generic.DIAGRAM_TYPE_TO_CONNECTOR_NAMES[diagram.type]:
            collector = default.collector
        else:
            collector = portless.collector
    except KeyError:
        logger.error(
            "Handling unknown diagram type %r. Default collector is used.",
            diagram.type,
        )
        collector = default.collector

    return collector(diagram, params)
