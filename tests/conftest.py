# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

"""Global fixtures for pytest"""
import io
import pathlib
import sys

import capellambse
import pytest

TEST_ROOT = pathlib.Path(__file__).parent / "data"
TEST_MODEL = "ContextDiagram.aird"


@pytest.fixture
def model(monkeypatch) -> capellambse.MelodyModel:
    """Return test model"""
    monkeypatch.setattr(sys, "stderr", io.StringIO)
    return capellambse.MelodyModel(TEST_ROOT / TEST_MODEL)
