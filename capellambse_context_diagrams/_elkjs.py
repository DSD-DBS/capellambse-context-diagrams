# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
ELK data model implemented as `typings.TypedDict`s and subprocess
callers to check if elkjs can be installed via npm. The high level
function is [call_elkjs][capellambse_context_diagrams._elkjs.call_elkjs].
"""
from __future__ import annotations

import collections.abc as cabc
import copy
import json
import logging
import os
import shutil
import subprocess
import typing as t
from pathlib import Path

import capellambse
import pydantic

__all__ = [
    "call_elkjs",
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
]

log = logging.getLogger(__name__)

NODE_HOME = Path(capellambse.dirs.user_cache_dir, "elkjs", "node_modules")
PATH_TO_ELK_JS = Path(__file__).parent / "elk.js"
REQUIRED_NPM_PKG_VERSIONS: t.Dict[str, str] = {
    "elkjs": "0.9.2",
}
"""npm package names and versions required by this Python module."""

LayoutOptions = cabc.MutableMapping[str, t.Union[str, int, float]]
ImmutableLayoutOptions = cabc.Mapping[str, t.Union[str, int, float]]
LAYOUT_OPTIONS: ImmutableLayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.direction": "RIGHT",
    "hierarchyHandling": "INCLUDE_CHILDREN",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "layered.nodePlacement.strategy": "BRANDES_KOEPF",
    "layered.considerModelOrder.strategy": "NODES_AND_EDGES",
    "spacing.labelNode": "0.0",
}
"""
Available (and possibly useful) Global Options to configure ELK layouting.

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
LABEL_LAYOUT_OPTIONS = {"nodeLabels.placement": "OUTSIDE, V_BOTTOM, H_CENTER"}
"""Options for labels to configure ELK layouting."""


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

    width: t.Union[int, float] = 0
    height: t.Union[int, float] = 0


class ELKInputLabel(BaseELKModel):
    """Label data that can be fed to ELK."""

    text: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)
    width: t.Union[int, float] = 0
    height: t.Union[int, float] = 0


class ELKInputPort(BaseELKModel):
    """Connector data that can be fed to ELK."""

    id: str
    layoutOptions: LayoutOptions = pydantic.Field(default_factory=dict)
    width: t.Union[int, float]
    height: t.Union[int, float]


class ELKInputEdge(BaseELKModel):
    """Exchange data that can be fed to ELK."""

    id: str
    sources: cabc.MutableSequence[str]
    targets: cabc.MutableSequence[str]
    labels: cabc.MutableSequence[ELKInputLabel] = pydantic.Field(
        default_factory=list
    )


class ELKPoint(BaseELKModel):
    """Point data in ELK."""

    x: t.Union[int, float]
    y: t.Union[int, float]


class ELKSize(BaseELKModel):
    """Size data in ELK."""

    width: t.Union[int, float]
    height: t.Union[int, float]


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


class ELKOutputJunction(ELKOutputElement):
    """Exchange-Junction that comes out of ELK."""

    type: t.Literal["junction"]
    children: cabc.MutableSequence[ELKOutputLabel] = pydantic.Field(
        default_factory=list
    )

    position: ELKPoint


class ELKOutputPort(ELKOutputDiagramElement):
    """Port that comes out of ELK."""

    type: t.Literal["port"]
    children: cabc.MutableSequence[ELKOutputLabel] = pydantic.Field(
        default_factory=list
    )


class ELKOutputLabel(ELKOutputDiagramElement):
    """Label that comes out of ELK."""

    type: t.Literal["label"]
    text: str


class ELKOutputEdge(ELKOutputElement):
    """Edge that comes out of ELK."""

    type: t.Literal["edge"]

    sourceId: str
    targetId: str
    routingPoints: cabc.MutableSequence[ELKPoint]
    children: cabc.MutableSequence[
        t.Union[ELKOutputLabel, ELKOutputJunction]
    ] = pydantic.Field(default_factory=list)


ELKOutputChild = t.Union[
    ELKOutputEdge,
    ELKOutputJunction,
    ELKOutputLabel,
    ELKOutputNode,
    ELKOutputPort,
]
"""Type alias for ELK output."""


class NodeJSError(RuntimeError):
    """An error happened during node execution."""


class ExecutableNotFoundError(NodeJSError, FileNotFoundError):
    """The required executable could not be found in the PATH."""


class NodeInstallationError(NodeJSError):
    """Installation of the node.js package failed."""


def _find_node_and_npm() -> None:
    """Find executables for ``node`` and ``npm``.

    Raises
    ------
    NodeJSError
        When ``node`` or ``npm`` cannot be found in any of the
        directories registered in the environment variable ``PATH``.
    """
    for i in ("node", "npm"):
        if shutil.which(i) is None:
            raise ExecutableNotFoundError(i)


def _get_installed_npm_pkg_versions() -> t.Dict[str, str]:
    """Read installed npm packages and versions.

    Returns
    -------
    dict
        Dictionary with installed npm package name (key), package
        version (val)
    """
    installed_npm_pkg_versions: t.Dict[str, str] = {}
    package_lock_file_path: Path = NODE_HOME.parent / "package-lock.json"
    if not package_lock_file_path.is_file():
        return installed_npm_pkg_versions
    package_lock: t.Dict[str, t.Any] = json.loads(
        package_lock_file_path.read_text()
    )
    if "packages" not in package_lock:
        return installed_npm_pkg_versions
    pkg_rel_path: str
    pkg_info: t.Dict[str, str]
    for pkg_rel_path, pkg_info in package_lock["packages"].items():
        if not pkg_rel_path.startswith("node_modules/"):
            continue
        if "version" not in pkg_info:
            log.warning(
                "Broken NPM lock file at %r: cannot find version of %s",
                str(package_lock_file_path),
                pkg_rel_path,
            )
            continue
        pkg_name: str = pkg_rel_path.replace("node_modules/", "")
        installed_npm_pkg_versions[pkg_name] = pkg_info["version"]
    return installed_npm_pkg_versions


def _install_npm_package(npm_pkg_name: str, npm_pkg_version: str) -> None:
    log.debug("Installing package %r into %s", npm_pkg_name, NODE_HOME)
    proc = subprocess.run(
        [
            "npm",
            "install",
            "--prefix",
            str(NODE_HOME.parent),
            f"{npm_pkg_name}@{npm_pkg_version}",
        ],
        executable=shutil.which("npm"),
        capture_output=True,
        check=False,
        text=True,
    )
    if proc.returncode:
        log.getChild("node").error("%s", proc.stderr)
        raise NodeInstallationError(npm_pkg_name)


def _install_required_npm_pkg_versions() -> None:
    try:
        NODE_HOME.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise RuntimeError(
            f"Cannot create elk.js install directory at: {NODE_HOME}.\n"
            "Make sure that important environment variables"
            " like $HOME are set correctly.\n"
            f"Failed due to {type(err).__name__}: {err}"
        ) from None
    installed = _get_installed_npm_pkg_versions()
    for pkg_name, pkg_version in REQUIRED_NPM_PKG_VERSIONS.items():
        if installed.get(pkg_name) != pkg_version:
            _install_npm_package(pkg_name, pkg_version)


def call_elkjs(elk_model: ELKInputData) -> ELKOutputData:
    """Call into elk.js to auto-layout the ``diagram``.

    Parameters
    ----------
    elk_dict
        The diagram data, sans layouting information

    Returns
    -------
    layouted_diagram
        The diagram data, augmented with layouting information
    """
    _find_node_and_npm()
    _install_required_npm_pkg_versions()

    ELKInputData.model_validate(elk_model, strict=True)
    proc = subprocess.run(
        ["node", str(PATH_TO_ELK_JS)],
        executable=shutil.which("node"),
        capture_output=True,
        check=False,
        input=elk_model.model_dump_json(exclude_defaults=True),
        text=True,
        env={**os.environ, "NODE_PATH": str(NODE_HOME)},
    )
    if proc.returncode:
        log.getChild("node").error("%s", proc.stderr)
        raise NodeJSError("elk.js process failed")

    return ELKOutputData.model_validate_json(proc.stdout, strict=True)


def get_global_layered_layout_options() -> LayoutOptions:
    """Return optimal ELKLayered configuration."""
    return copy.deepcopy(LAYOUT_OPTIONS)  # type: ignore[arg-type]
