# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Global fixtures for pytest."""

import io
import json
import os
import pathlib
import sys
import typing as t
from unittest import mock

import capellambse
import pytest

from capellambse_context_diagrams import _elkjs, context

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


def remove_ids_from_labels_and_junctions_in_elk_layout(
    elk_layout: _elkjs.ELKOutputData,
) -> dict[str, t.Any]:
    """Remove ids from labels and junctions in a layout from ELK."""
    layout = elk_layout.model_dump(exclude_defaults=True)

    def remove_select_ids(obj: t.Any) -> t.Any:
        if isinstance(obj, dict):
            if obj.get("type") in ["label", "junction"]:
                return {
                    k: remove_select_ids(v)
                    for k, v in obj.items()
                    if k != "id"
                }
            return {k: remove_select_ids(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [remove_select_ids(item) for item in obj]
        return obj

    return remove_select_ids(layout)


def add_deterministic_ids_to_elk_layout(elk_layout: str) -> dict[str, t.Any]:
    """Add sequential IDs to labels and junctions in an ELK layout."""
    layout = json.loads(elk_layout)
    next_id = 0

    def add_ids(obj):
        nonlocal next_id
        if not isinstance(obj, dict):
            return obj

        prefix = ""
        if obj.get("type") in {"label", "junction"}:
            prefix = f"{obj['type'][0]}"

        if prefix:
            obj["id"] = f"{prefix}_{next_id}"
            next_id += 1

        if "children" in obj:
            obj["children"] = [add_ids(child) for child in obj["children"]]

        return obj

    return add_ids(layout)


def text_size_mocker(
    text: str, fonttype: str = "", size: int = 12
) -> tuple[int, int]:
    """Mock text size calculation."""
    del fonttype
    return (len(text) * size // 2, size)


def write_test_data_file(
    file_path: pathlib.Path,
    data: _elkjs.ELKInputData | list[_elkjs.ELKInputData],
):
    """Write ELKInput test data to file.

    Note
    ----
    This is a helper function to write test data to files in case the
    expected test data changed.
    """
    import json

    if isinstance(data, list):
        data_dump = {
            "edges": [edge.model_dump(exclude_defaults=True) for edge in data]
        }
    else:
        data_dump = data.model_dump(exclude_defaults=True)

    if not file_path.is_file():
        file_path.touch()
    file_path.write_text(json.dumps(data_dump, indent=4), encoding="utf8")


def write_layout_test_data_file(
    file_path: pathlib.Path,
    data: _elkjs.ELKOutputData | list[_elkjs.ELKOutputData],
):
    """Write layout test data to file.

    Note
    ----
    This is a helper function to write test data to files in case the
    expected test data changed.
    """
    import json

    if isinstance(data, list):
        data_dump = {
            "edges": [
                remove_ids_from_labels_and_junctions_in_elk_layout(edge)
                for edge in data
            ]
        }
    else:
        data_dump = remove_ids_from_labels_and_junctions_in_elk_layout(data)

    if not file_path.is_file():
        file_path.touch()
    file_path.write_text(json.dumps(data_dump, indent=4), encoding="utf8")


def compare_elk_input_data(
    data: _elkjs.ELKInputData, expected: _elkjs.ELKInputData
) -> bool:
    return data.model_dump(exclude_defaults=True) == expected.model_dump(
        exclude_defaults=True
    )


@mock.patch("capellambse.helpers.extent_func", text_size_mocker)
def generic_collecting_test(
    model: capellambse.MelodyModel,
    params: tuple[str, str, dict[str, t.Any]],
    data_root: pathlib.Path,
    diagram_attr: str,
) -> tuple[
    _elkjs.ELKInputData
    | tuple[
        _elkjs.ELKInputData, _elkjs.ELKInputData | list[_elkjs.ELKInputEdge]
    ],
    _elkjs.ELKInputData,
]:
    """Test collecting test.

    Parameters
    ----------
    model
        The MelodyModel instance.
    params
        Tuple consisting of (UUID, file_name, render_params).
    data_root
        Path to the JSON input files.
    diagram_attr
        The attribute name of the diagram.
    extra_suffix
        Optional suffix for an extra file.
    extra_assert
        Optional function to assert a statement with an extra file.
    """
    uuid, file_name, render_params = params
    obj = model.by_uuid(uuid)
    file_path = data_root / file_name
    if (
        os.getenv("CAPELLAMBSE_CONTEXT_DIAGRAMS_WRITE_TEST_FILES", "false")
        == "true"
    ):
        write_test_data_file(
            file_path, getattr(obj, diagram_attr).elk_input_data(render_params)
        )
    data_text = file_path.read_text(encoding="utf8")
    expected_main = _elkjs.ELKInputData.model_validate_json(data_text)
    return getattr(obj, diagram_attr).elk_input_data(
        render_params
    ), expected_main


def generic_layouting_test(
    params: tuple[str, str, dict[str, t.Any]],
    data_root: pathlib.Path,
    layout_root: pathlib.Path,
):
    """Test layouting ELK input data.

    Parameters
    ----------
    params
        Tuple consisting of (UUID, file_name, render_params).
    data_root
        Path to the JSON input files.
    layout_root
        Path to the expected layout JSON files.
    """
    _, file_name, _ = params
    test_data = (data_root / file_name).read_text(encoding="utf8")
    data = _elkjs.ELKInputData.model_validate_json(test_data)

    layout = context.try_to_layout(data)
    if (
        os.getenv("CAPELLAMBSE_CONTEXT_DIAGRAMS_WRITE_TEST_FILES", "false")
        == "true"
    ):
        write_layout_test_data_file(layout_root / file_name, layout)

    expected_layout_data = (layout_root / file_name).read_text(encoding="utf8")
    expected: dict[str, t.Any] = json.loads(expected_layout_data)
    assert (
        remove_ids_from_labels_and_junctions_in_elk_layout(layout) == expected
    )


def generic_serializing_test(
    model: capellambse.MelodyModel,
    params: tuple[str, str, dict[str, t.Any]],
    layout_root: pathlib.Path,
    diagram_attr: str,
):
    """Test serializing ELKOutput data, i.e. layout.

    Parameters
    ----------
    model
        The MelodyModel instance.
    params
        Tuple consisting of (UUID, file_name, render_params).
    layout_root
        Path to the layout JSON files.
    diagram_attr
        The attribute name of the diagram.
    """
    uuid, file_name, render_params = params
    obj = model.by_uuid(uuid)
    diag = getattr(obj, diagram_attr)
    for key, value in render_params.items():
        setattr(diag, f"_{key}", value)

    layout_datastring = (layout_root / file_name).read_text(encoding="utf8")
    layout_data = add_deterministic_ids_to_elk_layout(layout_datastring)
    layout = _elkjs.ELKOutputData.model_validate(layout_data, strict=True)

    diag.serializer.make_diagram(layout)
