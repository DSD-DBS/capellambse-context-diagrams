# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import typing as t

import capellambse
import pytest
import yaml

from capellambse_context_diagrams.collectors import (
    collect_free_context,
    default,
    portless,
)

# pylint: disable-next=relative-beyond-top-level
from .conftest import TEST_ROOT

CONTEXT_PATH = TEST_ROOT / "context"
ContextInfo = t.Union[default.ContextInfo, portless.ContextInfo]
ExpectedConnectionInfo = dict[t.Literal["input", "output"], list[t.Any]]


def load_context_description(name: str) -> dict[str, t.Any]:
    return yaml.safe_load((CONTEXT_PATH / f"{name}.yaml").read_bytes())


def build_expected_context(
    model: capellambse.MelodyModel,
    expected: list[tuple[str, ExpectedConnectionInfo]],
) -> list[ContextInfo]:
    return [
        portless.ContextInfo(
            element=model.by_uuid(eid),
            connections={
                k: [model.by_uuid(cid) for cid in cids]
                for k, cids in connections.items()
            },
        )
        for eid, connections in expected
    ]


@pytest.mark.parametrize(
    "uuid,description,expected",
    [
        pytest.param(
            "da08ddb6-92ba-4c3b-956a-017424dbfe85",
            load_context_description("operationalcapability"),
            [
                (
                    "d3e1ce63-fad9-4eaa-8e70-959eb114cbc3",
                    {
                        "output": [
                            "2952e76c-e227-4075-ad73-9d5fa120ab98",
                            "3f119b35-8873-4ffb-8fac-d3fe3a9542da",
                        ],
                        "input": ["ef8b3d24-54b0-4654-bd0a-97584f58d457"],
                    },
                ),
                (
                    "f6a9376c-53d3-4950-8ec9-420c0af4ca46",
                    {
                        "output": [],
                        "input": [
                            "6b2e4618-7671-4c09-837d-0b5b43a3ce90",
                            "ddbfd060-6118-48bc-b591-ed51872e0b45",
                            "bb8b380c-fe44-4049-ad27-1f2dffcfa65e",
                        ],
                    },
                ),
                (
                    "5419c967-8d8d-44de-af9a-5144f65eb891",
                    {
                        "output": ["7468616d-eb61-4572-bfb7-ac4c732bb316"],
                        "input": [
                            "e44f5ecb-d30d-4ba7-b9d6-a71a4e1eca14",
                            "4a3d2744-19ef-41bc-abef-798099b89eb2",
                        ],
                    },
                ),
                (
                    "1477b800-8da5-4889-b112-35e2353c4675",
                    {
                        "output": ["2d07b314-2162-4d29-9ff1-f16e9b503f3d"],
                        "input": [],
                    },
                ),
                (
                    "f3577d00-01bb-405c-81c9-7bdc2dcdcdfc",
                    {
                        "output": ["11033438-7962-43be-9ead-c98900a7eaa5"],
                        "input": [],
                    },
                ),
            ],
            id="Middle",
        ),
        pytest.param(
            "9390b7d5-598a-42db-bef8-23677e45ba06",
            load_context_description("capability"),
            [
                (
                    "5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6",
                    {
                        "output": [],
                        "input": ["4513c8cd-b94b-4bde-bd00-4c18aaf600ff"],
                    },
                ),
                (
                    "562c5128-5acd-45cc-8b49-1d8d686f450a",
                    {
                        "output": [
                            "992c4ba5-0165-470d-b2d0-f117e00a645c",
                            "504c92c4-dc31-4065-9a82-31f277e59acb",
                        ],
                        "input": [],
                    },
                ),
                (
                    "9390b7d5-598a-42db-bef8-23677e45ba06",
                    {
                        "output": ["41cf3250-187b-44ab-9e7e-7c0d1fd12f8a"],
                        "input": [],
                    },
                ),
                (
                    "da12377b-fb70-4441-8faa-3a5c153c5de2",
                    {
                        "output": ["8f1d649c-8ac7-4ed1-b8c1-06faaf5c0eac"],
                        "input": [],
                    },
                ),
                (
                    "344a405e-c7e5-4367-8a9a-41d3d9a27f81",
                    {
                        "output": ["30f5613f-9611-4b36-9f46-aacfa00c687a"],
                        "input": [],
                    },
                ),
            ],
            id="Capability",
        ),
        pytest.param(
            "5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6",
            load_context_description("mission"),
            [
                (
                    "9390b7d5-598a-42db-bef8-23677e45ba06",
                    {
                        "output": ["4513c8cd-b94b-4bde-bd00-4c18aaf600ff"],
                        "input": [],
                    },
                ),
                (
                    "344a405e-c7e5-4367-8a9a-41d3d9a27f81",
                    {
                        "output": ["4ec609b6-e3bf-4be1-ba09-14da9c920ef3"],
                        "input": [],
                    },
                ),
            ],
            id="Top Secret",
        ),
    ],
)
def test_free_context_collection(
    model: capellambse.MelodyModel,
    uuid: str,
    description: dict[str, t.Any],
    expected: list[tuple[str, ExpectedConnectionInfo]],
) -> None:
    target = model.by_uuid(uuid)
    expected_context = build_expected_context(model, expected)

    context = list(
        collect_free_context(
            model, target, description, portless.context_collector
        )
    )

    assert set(context) == set(expected_context)
