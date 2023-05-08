# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

import capellambse
import pytest
from capellambse.model.layers import ctx, oa

# pylint: disable-next=relative-beyond-top-level, useless-suppression
from .conftest import SYSTEM_ANALYSIS_PARAMS  # type: ignore[import]

TEST_TYPES = (oa.OperationalCapability, ctx.Capability, ctx.Mission)


@pytest.mark.parametrize("uuid", SYSTEM_ANALYSIS_PARAMS)
def test_context_diagrams(model: capellambse.MelodyModel, uuid: str) -> None:
    obj = model.by_uuid(uuid)
    assert isinstance(obj, TEST_TYPES), "Precondition failed"

    diag = obj.context_diagram

    assert diag.nodes
