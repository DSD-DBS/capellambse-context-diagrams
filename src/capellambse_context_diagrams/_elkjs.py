# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functionality for the ELK data model and the call to elkjs.

Implementation of the data model and subprocess callers to check if
elkjs can be installed via npm.

The high level function is
[call_elkjs][capellambse_context_diagrams._elkjs.call_elkjs].
"""

from __future__ import annotations

import collections.abc as cabc
import copy
import enum
import logging
import pathlib
import platform
import subprocess
import typing as t

import pydantic

__all__ = [
    "ELKInputChild",
    "ELKInputData",
    "ELKInputEdge",
    "ELKInputLabel",
    "ELKInputPort",
    "ELKOutputChild",
    "ELKOutputData",
    "ELKOutputEdge",
    "ELKOutputLabel",
    "ELKOutputNode",
    "ELKOutputPort",
    "ELKPoint",
    "ELKSize",
    "call_elkjs",
]

log = logging.getLogger(__name__)

LayoutOptions = cabc.MutableMapping[str, str | int | float]
ImmutableLayoutOptions = cabc.Mapping[str, str | int | float]
LAYOUT_OPTIONS: ImmutableLayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.direction": "RIGHT",
    "hierarchyHandling": "INCLUDE_CHILDREN",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "layered.nodePlacement.strategy": "BRANDES_KOEPF",
    "spacing.labelNode": "0.0",
}
"""Available (and possibly useful) Global Options to configure ELK layouting.

See Also
--------
[get_global_layered_layout_options][capellambse_context_diagrams._elkjs.get_global_layered_layout_options] :
    A function that instantiates this class with well-tested settings.
"""
CLASS_TREE_LAYOUT_OPTIONS: ImmutableLayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.direction": "RIGHT",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "layered.nodePlacement.strategy": "BRANDES_KOEPF",
    "spacing.labelNode": "0.0",
    "spacing.edgeNode": 20,
    "compaction.postCompaction.strategy": "LEFT_RIGHT_CONSTRAINT_LOCKING",
    "layered.considerModelOrder.components": "MODEL_ORDER",
    "separateConnectedComponents": False,
}
RECT_PACKING_LAYOUT_OPTIONS: ImmutableLayoutOptions = {
    "algorithm": "elk.rectpacking",
    "nodeSize.constraints": "[NODE_LABELS, MINIMUM_SIZE]",
    "widthApproximation.targetWidth": 1,  # width / height
    "elk.contentAlignment": "V_TOP H_CENTER",
}
LABEL_LAYOUT_OPTIONS: LayoutOptions = {
    "nodeLabels.placement": "OUTSIDE, V_BOTTOM, H_CENTER"
}
"""Options for labels to configure ELK layouting."""
EDGE_STRAIGHTENING_LAYOUT_OPTIONS: LayoutOptions = {
    "layered.priority.straightness": "10"
}
"""Options for increasing the edge straightness priority."""


class PORT_LABEL_POSITION(enum.Enum):
    """Position of port labels.

    Attributes
    ----------
    OUTSIDE
        The label is placed outside the port.
    INSIDE
        The label is placed inside the port owner box.
    NEXT_TO_PORT_IF_POSSIBLE
        The label is placed next to the port if space allows.
    ALWAYS_SAME_SIDE
        The label is always placed on the same side of the port.
    ALWAYS_OTHER_SAME_SIDE
        The label is always placed on the opposite side, but on the same
        axis.
    SPACE_EFFICIENT
        The label is positioned in the most space-efficient location.
    """

    OUTSIDE = enum.auto()
    INSIDE = enum.auto()
    NEXT_TO_PORT_IF_POSSIBLE = enum.auto()
    ALWAYS_SAME_SIDE = enum.auto()
    ALWAYS_OTHER_SAME_SIDE = enum.auto()
    SPACE_EFFICIENT = enum.auto()


class BaseELKModel(pydantic.BaseModel):
    """Base class for ELK models."""

    model_config = pydantic.ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )


class ELKInputData(BaseELKModel):
    """Data that can be fed to ELK."""

    id: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)
    children: cabc.MutableSequence[ELKInputChild] = pydantic.Field(
        default_factory=list
    )
    edges: cabc.MutableSequence[ELKInputEdge] = pydantic.Field(
        default_factory=list
    )


class ELKInputChild(ELKInputData):
    """Children of either `ELKInputData` or `ELKInputChild`."""

    labels: cabc.MutableSequence[ELKInputLabel] = pydantic.Field(
        default_factory=list
    )
    ports: cabc.MutableSequence[ELKInputPort] = pydantic.Field(
        default_factory=list
    )

    width: int | float = 0
    height: int | float = 0


class ELKInputLabel(BaseELKModel):
    """Label data that can be fed to ELK."""

    text: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)
    width: int | float = 0
    height: int | float = 0


class ELKInputPort(BaseELKModel):
    """Connector data that can be fed to ELK."""

    id: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)
    width: int | float
    height: int | float
    labels: cabc.MutableSequence[ELKInputLabel] = pydantic.Field(
        default_factory=list
    )


class ELKInputEdge(BaseELKModel):
    """Exchange data that can be fed to ELK."""

    id: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)

    sources: cabc.MutableSequence[str]
    targets: cabc.MutableSequence[str]
    labels: cabc.MutableSequence[ELKInputLabel] = pydantic.Field(
        default_factory=list
    )


class ELKPoint(BaseELKModel):
    """Point data in ELK."""

    x: int | float
    y: int | float


class ELKSize(BaseELKModel):
    """Size data in ELK."""

    width: int | float
    height: int | float


class ELKOutputElement(BaseELKModel):
    """Base class for all elements that comes out of ELK."""

    id: str

    style: dict[str, t.Any] = pydantic.Field(default_factory=dict)


class ELKOutputDiagramElement(ELKOutputElement):
    """Class for positioned and sized elements that come out of ELK."""

    position: ELKPoint
    size: ELKSize


class ELKOutputData(ELKOutputElement):
    """Data that comes from ELK."""

    type: t.Literal["graph"]
    children: cabc.MutableSequence[ELKOutputChild] = pydantic.Field(
        default_factory=list
    )


class ELKOutputNode(ELKOutputDiagramElement):
    """Node that comes out of ELK."""

    type: t.Literal["node"]
    children: cabc.MutableSequence[ELKOutputChild] = pydantic.Field(
        default_factory=list
    )
    context: list[str] = pydantic.Field(default_factory=list)


class ELKOutputJunction(ELKOutputElement):
    """Exchange-Junction that comes out of ELK."""

    type: t.Literal["junction"]
    children: cabc.MutableSequence[ELKOutputLabel] = pydantic.Field(
        default_factory=list
    )

    position: ELKPoint
    context: list[str] = pydantic.Field(default_factory=list)


class ELKOutputPort(ELKOutputDiagramElement):
    """Port that comes out of ELK."""

    type: t.Literal["port"]
    children: cabc.MutableSequence[ELKOutputLabel] = pydantic.Field(
        default_factory=list
    )
    context: list[str] = pydantic.Field(default_factory=list)


class ELKOutputLabel(ELKOutputDiagramElement):
    """Label that comes out of ELK."""

    type: t.Literal["label"]
    text: str
    context: list[str] = pydantic.Field(default_factory=list)


class ELKOutputEdge(ELKOutputElement):
    """Edge that comes out of ELK."""

    type: t.Literal["edge"]

    sourceId: str
    targetId: str
    routingPoints: cabc.MutableSequence[ELKPoint]
    children: cabc.MutableSequence[ELKOutputLabel | ELKOutputJunction] = (
        pydantic.Field(default_factory=list)
    )
    context: list[str] = pydantic.Field(default_factory=list)


ELKOutputChild = (
    ELKOutputEdge
    | ELKOutputJunction
    | ELKOutputLabel
    | ELKOutputNode
    | ELKOutputPort
)
"""Type alias for ELK output."""


class NodeJSError(RuntimeError):
    """An error happened during node execution."""


class ExecutableNotFoundError(NodeJSError, FileNotFoundError):
    """The required executable could not be found in the PATH."""

def get_binary_path() -> pathlib.Path:
    pkg_dir = pathlib.Path(__file__).parent
    system = platform.system().lower()

    # The binary name will include .exe on Windows
    binary_name = "elk.exe" if system == "windows" else "elk"
    binary_path = pkg_dir / binary_name

    if not binary_path.exists():
        raise RuntimeError(
            f"Binary not found at {binary_path}. This might indicate an "
            "incomplete installation or unsupported platform."
        )

    # Ensure the binary is executable on Unix-like systems
    if system != "windows":
        binary_path.chmod(binary_path.stat().st_mode | 0o111)

    return binary_path


proc = subprocess.Popen(
    ["elk"],
    executable=get_binary_path(),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


def call_elkjs(elk_model: ELKInputData) -> ELKOutputData:
    """Call into elk.js to auto-layout the ``diagram``.

    Parameters
    ----------
    elk_model
        The diagram data, sans layouting information

    Returns
    -------
    layouted_diagram
        The diagram data, augmented with layouting information
    """
    # _find_node_and_npm()
    # _install_required_npm_pkg_versions()

    ELKInputData.model_validate(elk_model, strict=True)
    proc.stdin.write(elk_model.model_dump_json(exclude_defaults=True) + '\n')
    proc.stdin.flush()  # Ensure the input is flushed
    response = proc.stdout.readline()
    return ELKOutputData.model_validate_json(response, strict=True)

def get_global_layered_layout_options() -> LayoutOptions:
    """Return optimal ELKLayered configuration."""
    return copy.deepcopy(LAYOUT_OPTIONS)  # type: ignore[arg-type]
