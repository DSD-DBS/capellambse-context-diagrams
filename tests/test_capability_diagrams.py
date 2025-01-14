# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import capellambse.metamodel as mm
import pytest

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import SYSTEM_ANALYSIS_PARAMS  # type: ignore[import-untyped]

TEST_TYPES = (mm.oa.OperationalCapability, mm.sa.Capability, mm.sa.Mission)


@pytest.mark.parametrize("uuid", SYSTEM_ANALYSIS_PARAMS)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)
    assert isinstance(obj, TEST_TYPES), "Precondition failed"

    diag = obj.context_diagram

    assert diag.nodes
