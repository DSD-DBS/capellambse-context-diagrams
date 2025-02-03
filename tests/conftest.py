# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Global fixtures for pytest."""

import io
import pathlib
import sys
import typing as t

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs

TEST_ROOT = pathlib.Path(__file__).parent / "data"
TEST_ELK_INPUT_ROOT = TEST_ROOT / "elk_input"
TEST_ELK_LAYOUT_ROOT = TEST_ROOT / "elk_layout"
TEST_MODEL = "ContextDiagram.aird"
SYSTEM_ANALYSIS_PARAMS = [
    pytest.param(
        "da08ddb6-92ba-4c3b-956a-017424dbfe85", id="OperationalCapability"
    ),
    pytest.param("9390b7d5-598a-42db-bef8-23677e45ba06", id="Capability"),
    pytest.param("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6", id="Mission"),
]


@pytest.fixture
def model(monkeypatch) -> capellambse.MelodyModel:
    """Return test model."""
    monkeypatch.setattr(sys, "stderr", io.StringIO)
    return capellambse.MelodyModel(TEST_ROOT / TEST_MODEL)


def remove_ids_from_elk_layout(
    elk_layout: _elkjs.ELKOutputData,
) -> dict[str, t.Any]:
    layout_dict = elk_layout.model_dump(exclude_defaults=True)

    def remove_ids(obj: t.Any) -> t.Any:
        if isinstance(obj, dict):
            return {k: remove_ids(v) for k, v in obj.items() if k != "id"}
        if isinstance(obj, list):
            return [remove_ids(item) for item in obj]
        return obj

    return remove_ids(layout_dict)
