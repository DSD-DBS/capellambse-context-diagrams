# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Functionality for the ELK data model and the call to elkjs.

Implementation of the data model and subprocess callers to check for
elkjs binaries or deno support.

The ELKManager class is the manager for the ELK subprocess. It is
responsible for spawning the subprocess, downloading the binary if
necessary, and calling into the subprocess.

The elk_manager instance is the global instance of the ELKManager class.
It can be used to call into elkjs.

"""

from __future__ import annotations

import atexit
import collections.abc as cabc
import contextlib
import copy
import enum
import importlib.metadata
import logging
import pathlib
import platform
import shutil
import subprocess
import threading
import typing as t

import platformdirs
import pydantic
import requests
from capellambse import model as m

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
    "elk_manager",
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


@m.stringy_enum
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


class ELKManager:
    _proc: subprocess.Popen | None
    _lock: threading.Lock

    def __init__(self):
        self._proc = None
        self._lock = threading.Lock()

    @property
    def runtime_version(self) -> str:
        """The version of the elkjs runtime package to download."""
        package_version = importlib.metadata.version(
            "capellambse_context_diagrams"
        )
        if ".dev" in package_version:
            package_version, _ = package_version.split(".dev", 1)
            head, tail = package_version.rsplit(".", 1)
            assert tail != "0"
            package_version = f"{head}.{int(tail) - 1}"
        return package_version

    @property
    def binary_name(self):
        system = platform.system().lower()
        machine = platform.machine().lower()

        build_mapping = {
            ("windows", "amd64"): "x86_64-pc-windows-msvc",
            ("darwin", "x86_64"): "x86_64-apple-darwin",
            ("darwin", "arm64"): "aarch64-apple-darwin",
            ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
            ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
        }

        build = build_mapping.get((system, machine))
        if not build:
            raise RuntimeError(f"Unsupported platform: {system} {machine}")

        return f"elk-v{self.runtime_version}-{build}{'.exe' if system == 'windows' else ''}"

    @property
    def binary_path(self):
        cache_dir = platformdirs.user_cache_dir("capellambse_context_diagrams")
        return pathlib.Path(cache_dir) / self.binary_name

    def download_binary(self, force=False):
        if self.binary_path.exists() and not force:
            log.debug(
                "elk.js helper binary already exists at %s", self.binary_path
            )
            return

        log.debug("Downloading elk.js helper binary")
        self.binary_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/DSD-DBS/capellambse-context-diagrams/releases/download/v{self.runtime_version}/{self.binary_name}"
        response = requests.get(url)
        response.raise_for_status()
        with open(self.binary_path, "wb") as f:
            f.write(response.content)
        log.debug("Downloaded elk.js helper binary to %s", self.binary_path)

        # Ensure the binary is executable on Unix-like systems
        system = platform.system().lower()
        if system != "windows":
            self.binary_path.chmod(self.binary_path.stat().st_mode | 0o111)

    def _spawn_process_binary(self):
        self.download_binary()

        log.debug("Spawning elk.js helper process at %s", self.binary_path)
        self._proc = subprocess.Popen(
            [self.binary_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if not self._proc.stdout:
            raise RuntimeError("Failed to start elk.js helper process")

        line = self._proc.stdout.readline()
        if line.strip() != "--- ELK layouter started ---":
            raise RuntimeError("Failed to start elk.js helper process")
        log.debug("Spawned elk.js helper process")

    def _spawn_process_deno(self):
        log.debug("Spawning elk.js helper process using deno")
        deno_location = shutil.which("deno")
        script_location = pathlib.Path(__file__).parent / "interop" / "elk.ts"
        if deno_location is None:
            raise RuntimeError("Deno is not installed")

        self._proc = subprocess.Popen(
            [
                deno_location,
                "run",
                "--allow-read",
                "--allow-net",
                "--allow-env",
                "--no-check",
                "--quiet",
                script_location,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if not self._proc.stdout:
            raise RuntimeError(
                "Failed to start elk.js helper process using deno"
            )

        line = self._proc.stdout.readline()
        if line.strip() != "--- ELK layouter started ---":
            raise RuntimeError(
                "Failed to start elk.js helper process using deno"
            )
        log.debug("Spawned elk.js helper process using deno")

    def spawn_process(self):
        """Spawn the elk.js process.

        The preferenced order is:
        binary (downloaded) > deno > binary (needs download)
        """

        if self.binary_path.exists() or shutil.which("deno") is None:
            self._spawn_process_binary()
        else:
            self._spawn_process_deno()

    def terminate_process(self):
        log.debug("Terminating elk.js helper process")
        if self._proc is not None:
            self._proc.terminate()
            self._proc = None
            log.debug("Terminated elk.js helper process")
        else:
            log.debug("No elk.js helper process to terminate")

    @contextlib.contextmanager
    def get_process(self) -> cabc.Iterator[tuple[t.IO[str], t.IO[str]]]:
        with self._lock:
            if self._proc is None:
                self.spawn_process()
                assert self._proc is not None
            assert self._proc.stdin is not None
            assert self._proc.stdout is not None
            yield self._proc.stdin, self._proc.stdout

    def call_elkjs(self, elk_model: ELKInputData) -> ELKOutputData:
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
        ELKInputData.model_validate(elk_model, strict=True)
        request = elk_model.model_dump_json(exclude_defaults=True) + "\n"
        with self.get_process() as (stdin, stdout):
            stdin.write(request)
            stdin.flush()
            response = stdout.readline()
        return ELKOutputData.model_validate_json(response, strict=True)


elk_manager = ELKManager()

atexit.register(elk_manager.terminate_process)


def get_global_layered_layout_options() -> LayoutOptions:
    """Return optimal ELKLayered configuration."""
    return copy.deepcopy(LAYOUT_OPTIONS)  # type: ignore[arg-type]
