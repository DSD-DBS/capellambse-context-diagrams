# SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import typing as t

import capellambse
import pytest
import yaml

from capellambse_context_diagrams import collectors
from capellambse_context_diagrams.collectors import default, portless

# pylint: disable-next=relative-beyond-top-level
from .conftest import TEST_ROOT

CONTEXT_PATH = TEST_ROOT / "context"

ExpectedConnectionInfo = dict[t.Literal["input", "output"], list[t.Any]]


def load_context_description(name: str) -> dict[str, t.Any]:
    return yaml.safe_load((CONTEXT_PATH / f"{name}.yaml").read_bytes())


def build_expected_context(
    model: capellambse.MelodyModel, builder: ContextInfoBuilder
) -> list[collectors.ContextInfo]:
    if builder.collector == portless.context_collector:
        return [
            portless.ContextInfo(
                element=model.by_uuid(eid),
                connections={
                    k: [model.by_uuid(cid) for cid in cids]
                    for k, cids in connections.items()
                },
            )
            for eid, connections in builder.content
        ]
    return [
        default.ContextInfo(
            element=model.by_uuid(eid),
            ports={
                k: [model.by_uuid(cid) for cid in cids]
                for k, cids in ports.items()
            },
        )
        for eid, ports in builder.content
    ]


class ContextInfoBuilder(t.NamedTuple):
    uuid: str
    description: dict[str, t.Any]
    collector: collectors.ContextCollector
    content: list[tuple[str, ExpectedConnectionInfo]]


SFUNC_CTX_BUILDER = ContextInfoBuilder(
    "a5642060-c9cc-4d49-af09-defaa3024bae",
    load_context_description("systemfunction"),
    default.port_context_collector,
    [
        (
            "1c304898-b1b7-49c4-8877-5ea3c9959b6e",
            {
                "output": [],
                "input": ["31e32de6-0f67-4922-9185-66706925cff8"],
            },
        ),
        (
            "ceffa011-7b66-4b3c-9885-8e075e312ffa",
            {
                "output": [
                    "28ced9df-b6f2-48a0-8bf3-81a7a5cd1b6b",
                    "af361e95-9a87-4b67-8d0c-74585c1d695a",
                ],
                "input": [],
            },
        ),
        (
            "8dc62b22-c2c8-4a0a-8e69-1dc5d8e1d44d",
            {
                "output": [],
                "input": ["554f4296-773b-4acb-a347-265fb16b401b"],
            },
        ),
    ],
)
LFUNC_CTX_BUILDER = ContextInfoBuilder(
    "7f138bae-4949-40a1-9a88-15941f827f8c",
    load_context_description("logicalfunction"),
    default.port_context_collector,
    [
        (
            "9d367e35-d826-4256-98b1-3278cc4c3ab8",
            {
                "output": [],
                "input": ["cd739c16-9f51-42b5-ace1-42e82acbf63a"],
            },
        ),
        (
            "a65281e5-83e9-4aad-a2c6-0c31d8b24477",
            {
                "output": ["dd98c04f-6e47-4989-bccf-7fa6cc51a28f"],
                "input": ["aac1f636-44cd-467a-8238-3c383f28351e"],
            },
        ),
    ],
)
SCOMP_CTX_BUILDER = ContextInfoBuilder(
    "344a405e-c7e5-4367-8a9a-41d3d9a27f81",
    load_context_description("systemcomponent"),
    default.port_context_collector,
    [
        (
            "da12377b-fb70-4441-8faa-3a5c153c5de2",
            {
                "output": [],
                "input": ["b2d2a4f1-0c21-45f4-918c-3d3c5e8af104"],
            },
        ),
        (
            "d4a22478-5717-4ca7-bfc9-9a193e6218a8",
            {
                "output": ["5e53616c-d3b6-4b2c-be23-6fb4229ddd20"],
                "input": [],
            },
        ),
        (
            "6241d0c5-65d2-4c0b-b79c-a2a8ed7273f6",
            {
                "output": ["74505eac-7abc-476d-8dec-ad68abb4b2a5"],
                "input": [],
            },
        ),
        (
            "230c4621-7e0a-4d0a-9db2-d4ba5e97b3df",
            {
                "output": ["898b878b-4392-499a-82f7-eb48e0f07e36"],
                "input": [],
            },
        ),
    ],
)
LCOMP_CTX_BUILDER = ContextInfoBuilder(
    "f632888e-51bc-4c9f-8e81-73e9404de784",
    load_context_description("logicalcomponent"),
    default.port_context_collector,
    [
        (
            "f8c9df04-fcd5-479d-814b-696fa6050231",
            {
                "output": [],
                "input": ["1286b0fe-dd57-46ba-8303-bd57eb04178d"],
            },
        ),
        (
            "37dfa5e6-a121-4ce9-8aa4-09a0c73dc2e9",
            {
                "output": ["58f89f0a-7647-4077-b29b-8fe2bf270f02"],
                "input": ["4cd7a9ba-afa2-47df-aa89-5b4ca5a5627a"],
            },
        ),
    ],
)
ENT_CTX_BUILDER = ContextInfoBuilder(
    "e37510b9-3166-4f80-a919-dfaac9b696c7",
    load_context_description("entity"),
    portless.context_collector,
    [
        (
            "a8c42033-fdf2-458f-bae9-1cfd1207c49f",
            {
                "output": ["6638ccd2-61cc-481e-bb23-4c1b147e1dbc"],
                "input": [],
            },
        )
    ],
)
MISS_CTX_BUILDER = ContextInfoBuilder(
    "5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6",
    load_context_description("mission"),
    portless.context_collector,
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
)
CAP_CTX_BUILDER = ContextInfoBuilder(
    "9390b7d5-598a-42db-bef8-23677e45ba06",
    load_context_description("capability"),
    portless.context_collector,
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
)
OCAP_CTX_BUILDER = ContextInfoBuilder(
    "da08ddb6-92ba-4c3b-956a-017424dbfe85",
    load_context_description("operationalcapability"),
    portless.context_collector,
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
)
ACT_CTX_BUILDER = ContextInfoBuilder(
    "0e0164c3-076e-42c1-8f82-7a43ab84385c",
    load_context_description("operationalactivity"),
    portless.context_collector,
    [
        (
            "8d8d235d-e030-4608-9508-68bb3818e7a4",
            {
                "output": [],
                "input": ["e3889e88-1d16-44f6-8f38-bb871ed4ace0"],
            },
        ),
        (
            "a5ba1fbc-59a3-4684-9043-3d5cd3dec5fe",
            {
                "output": [],
                "input": ["dd2d0dab-a35f-4104-91e5-b412f35cba15"],
            },
        ),
        (
            "8bcb11e6-443b-4b92-bec2-ff1d87a224e7",
            {
                "output": ["55b90f9a-c5af-47fc-9c1c-48090414d1f1"],
                "input": [],
            },
        ),
    ],
)


@pytest.mark.parametrize(
    "builder",
    [
        pytest.param(ACT_CTX_BUILDER, id="OperationalActivity [Make food]"),
        pytest.param(OCAP_CTX_BUILDER, id="OperationalCapability [Middle]"),
        pytest.param(CAP_CTX_BUILDER, id="Capability [Capability]"),
        pytest.param(MISS_CTX_BUILDER, id="Mission [Top Secret]"),
        pytest.param(ENT_CTX_BUILDER, id="Entity [Environment]"),
        pytest.param(LCOMP_CTX_BUILDER, id="LogicalComponent [Left]"),
        pytest.param(SCOMP_CTX_BUILDER, id="SystemComponent [Kevin Spacey]"),
        pytest.param(LFUNC_CTX_BUILDER, id="LogicalFunction [First]"),
        pytest.param(SFUNC_CTX_BUILDER, id="SystemFunction [Lost]"),
    ],
)
def test_free_context_collection_with_collectors(
    model: capellambse.MelodyModel, builder: ContextInfoBuilder
) -> None:
    """Test context collection from description using functions.

    The inputs/outputs are to be interpreted from the viewpoint of the
    object of interest.
    """
    target = model.by_uuid(builder.uuid)
    expected_context = build_expected_context(model, builder)

    context = list(
        collectors.collect_free_context(
            model, target, builder.description, builder.collector
        )
    )

    assert set(context) == set(expected_context)


@pytest.mark.parametrize(
    "builder",
    [
        pytest.param(ACT_CTX_BUILDER, id="OperationalActivity [Make food]"),
        pytest.param(OCAP_CTX_BUILDER, id="OperationalCapability [Middle]"),
        pytest.param(CAP_CTX_BUILDER, id="Capability [Capability]"),
        pytest.param(MISS_CTX_BUILDER, id="Mission [Top Secret]"),
        pytest.param(ENT_CTX_BUILDER, id="Entity [Environment]"),
        pytest.param(LCOMP_CTX_BUILDER, id="LogicalComponent [Left]"),
        pytest.param(SCOMP_CTX_BUILDER, id="SystemComponent [Kevin Spacey]"),
        pytest.param(LFUNC_CTX_BUILDER, id="LogicalFunction [First]"),
        pytest.param(SFUNC_CTX_BUILDER, id="SystemFunction [Lost]"),
    ],
)
def test_free_context_collection(
    model: capellambse.MelodyModel, builder: ContextInfoBuilder
) -> None:
    """Test context collection from description using translation.

    The inputs/outputs are to be interpreted from the viewpoint of the
    object of interest.
    """
    target = model.by_uuid(builder.uuid)
    expected_context = build_expected_context(model, builder)

    context = list(
        collectors.collect_free_context(model, target, builder.description)
    )

    assert set(context) == set(expected_context)
