# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""
ELK data model implemented as `typings.TypedDict`s and subprocess
callers to check if elkjs can be installed via npm. The high level
function is [call_elkjs][capellambse_context_diagrams._elkjs.call_elkjs].
"""
from __future__ import annotations

import collections.abc as cabc
import json
import logging
import os
import shutil
import subprocess
import typing as t
from pathlib import Path

import capellambse
import typing_extensions as te

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
    "elkjs": "0.8.1",
}
"""npm package names and versions required by this Python module."""

LayoutOptions = dict[str, t.Union[str, int, float]]
LAYOUT_OPTIONS: LayoutOptions = {
    "algorithm": "layered",
    "edgeRouting": "ORTHOGONAL",
    "elk.direction": "RIGHT",
    "hierarchyHandling": "INCLUDE_CHILDREN",
    "layered.edgeLabels.sideSelection": "ALWAYS_DOWN",
    "layered.nodePlacement.strategy": "BRANDES_KOEPF",
    "spacing.labelNode": "0.0",
}
"""
Available (and possibly useful) Global Options to configure ELK layouting.

See Also
--------
[get_global_layered_layout_options][capellambse_context_diagrams._elkjs.get_global_layered_layout_options] :
    A function that instantiates this class with well-tested settings.
"""
LABEL_LAYOUT_OPTIONS = {"nodeLabels.placement": "OUTSIDE, V_BOTTOM, H_CENTER"}
"""Options for labels to configure ELK layouting."""


class ELKInputData(te.TypedDict):
    """Data that can be fed to ELK."""

    id: str
    layoutOptions: cabc.MutableMapping[str, t.Union[str, int, float]]
    children: cabc.MutableSequence[ELKInputChild]  # type: ignore
    edges: cabc.MutableSequence[ELKInputEdge]


class ELKInputChild(te.TypedDict, total=False):
    """Children of either `ELKInputData` or `ELKInputChild`."""

    id: te.Required[str]
    layoutOptions: cabc.MutableMapping[str, t.Union[str, int, float]]
    children: cabc.MutableSequence[ELKInputChild]  # type: ignore
    edges: cabc.MutableSequence[ELKInputEdge]

    labels: te.NotRequired[cabc.MutableSequence[ELKInputLabel]]
    ports: cabc.MutableSequence[ELKInputPort]

    width: t.Union[int, float]
    height: t.Union[int, float]


class ELKInputLabel(te.TypedDict, total=False):
    """Label data that can be fed to ELK."""

    text: te.Required[str]
    layoutOptions: cabc.MutableMapping[str, t.Union[str, int, float]]
    width: t.Union[int, float]
    height: t.Union[int, float]


class ELKInputPort(t.TypedDict):
    """Connector data that can be fed to ELK."""

    id: str
    width: t.Union[int, float]
    height: t.Union[int, float]

    layoutOptions: cabc.MutableMapping[str, t.Any]


class ELKInputEdge(te.TypedDict):
    """Exchange data that can be fed to ELK"""

    id: str
    sources: cabc.MutableSequence[str]
    targets: cabc.MutableSequence[str]
    labels: te.NotRequired[cabc.MutableSequence[ELKInputLabel]]


class ELKPoint(t.TypedDict):
    """Point data in ELK."""

    x: t.Union[int, float]
    y: t.Union[int, float]


class ELKSize(t.TypedDict):
    """Size data in ELK."""

    width: t.Union[int, float]
    height: t.Union[int, float]


class ELKOutputData(t.TypedDict):
    """Data that comes from ELK."""

    id: str
    type: t.Literal["graph"]
    children: cabc.MutableSequence[ELKOutputChild]  # type: ignore


class ELKOutputNode(t.TypedDict):
    """Node that comes out of ELK."""

    id: str
    type: t.Literal["node"]
    children: cabc.MutableSequence[ELKOutputChild]  # type: ignore

    position: ELKPoint
    size: ELKSize


class ELKOutputJunction(t.TypedDict):
    """Exchange-Junction that comes out of ELK."""

    id: str
    type: t.Literal["junction"]

    position: ELKPoint
    size: ELKSize


class ELKOutputPort(t.TypedDict):
    """Port that comes out of ELK."""

    id: str
    type: t.Literal["port"]
    children: cabc.MutableSequence[ELKOutputLabel]

    position: ELKPoint
    size: ELKSize


class ELKOutputLabel(t.TypedDict):
    """Label that comes out of ELK."""

    id: str
    type: t.Literal["label"]
    text: str

    position: ELKPoint
    size: ELKSize


class ELKOutputEdge(t.TypedDict):
    """Edge that comes out of ELK."""

    id: str
    type: t.Literal["edge"]
    sourceId: str
    targetId: str
    routingPoints: cabc.MutableSequence[ELKPoint]
    children: cabc.MutableSequence[ELKOutputLabel]


ELKOutputChild = t.Union[  # type: ignore
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
    if not NODE_HOME.is_dir():
        NODE_HOME.mkdir(parents=True)
    installed = _get_installed_npm_pkg_versions()
    for pkg_name, pkg_version in REQUIRED_NPM_PKG_VERSIONS.items():
        if installed.get(pkg_name) != pkg_version:
            _install_npm_package(pkg_name, pkg_version)


def call_elkjs(elk_dict: ELKInputData) -> ELKOutputData:
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

    proc = subprocess.run(
        ["node", str(PATH_TO_ELK_JS)],
        executable=shutil.which("node"),
        capture_output=True,
        check=False,
        input=json.dumps(elk_dict),
        text=True,
        env={**os.environ, "NODE_PATH": str(NODE_HOME)},
    )
    if proc.returncode:
        log.getChild("node").error("%s", proc.stderr)
        raise NodeJSError("elk.js process failed")

    return json.loads(proc.stdout)


def get_global_layered_layout_options() -> LayoutOptions:
    """Return optimal ELKLayered configuration."""
    return LAYOUT_OPTIONS
