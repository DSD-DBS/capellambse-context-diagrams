# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Global fixtures for pytest."""

import io
import pathlib
import sys

import capellambse
import pytest

TEST_ROOT = pathlib.Path(__file__).parent / "data"
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
