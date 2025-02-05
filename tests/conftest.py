# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Global fixtures for pytest."""

import collections.abc as cabc
import io
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


def remove_ids_from_elk_layout(
    elk_layout: _elkjs.ELKOutputData,
) -> dict[str, t.Any]:
    """Remove ids from a layout from ELK."""
    layout_dict = elk_layout.model_dump(exclude_defaults=True)

    def remove_ids(obj: t.Any) -> t.Any:
        if isinstance(obj, dict):
            return {k: remove_ids(v) for k, v in obj.items() if k != "id"}
        if isinstance(obj, list):
            return [remove_ids(item) for item in obj]
        return obj

    return remove_ids(layout_dict)


def text_size_mocker(
    text: str, fonttype: str = "", size: int = 12
) -> tuple[int, int]:
    """Mock text size calculation."""
    del fonttype
    return (len(text) * size // 2, size)


def write_test_data_file(
    file_path: pathlib.Path,
    data: _elkjs.BaseELKModel | list[_elkjs.BaseELKModel],
):
    """Write test data to file.

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

    file_path.write_text(json.dumps(data_dump, indent=4), encoding="utf8")


def generic_collecting_test(
    model: capellambse.MelodyModel,
    params: tuple[str, str, dict[str, t.Any]],
    data_root: pathlib.Path,
    diagram_attr: str,
    extra_suffix: str | None = None,
    extra_assert: cabc.Callable[
        [str, list[_elkjs.ELKInputEdge] | _elkjs.ELKOutputData], bool
    ]
    | None = None,
):
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
    uuid, file_name, _ = params
    obj = model.by_uuid(uuid)
    file_path = data_root / file_name
    data_text = file_path.read_text(encoding="utf8")
    expected_main = _elkjs.ELKInputData.model_validate_json(data_text)
    expected_extra_file: pathlib.Path | None = None
    if extra_suffix:
        expected_extra_file = data_root / (file_path.stem + extra_suffix)
        expected_extra = expected_extra_file.read_text(encoding="utf8")

    with mock.patch("capellambse.helpers.extent_func") as mock_ext:
        mock_ext.side_effect = text_size_mocker
        result = getattr(obj, diagram_attr).elk_input_data({})

    if extra_suffix and extra_assert and expected_extra_file:
        main_output, extra_output = result
        assert main_output.model_dump(
            exclude_defaults=True
        ) == expected_main.model_dump(exclude_defaults=True)
        assert extra_assert(expected_extra, extra_output)
        return

    assert result.model_dump(
        exclude_defaults=True
    ) == expected_main.model_dump(exclude_defaults=True)


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
    expected_layout_data = (layout_root / file_name).read_text(encoding="utf8")
    expected = _elkjs.ELKOutputData.model_validate_json(expected_layout_data)

    layout = context.try_to_layout(data)

    assert remove_ids_from_elk_layout(layout) == remove_ids_from_elk_layout(
        expected
    )


def generic_serializing_test(
    model: capellambse.MelodyModel,
    params: tuple[str, str, dict[str, t.Any]],
    layout_root: pathlib.Path,
    diagram_attr: str,
) -> bool:
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

    layout_data = (layout_root / file_name).read_text(encoding="utf8")
    layout = _elkjs.ELKOutputData.model_validate_json(layout_data)
    diag.serializer.make_diagram(layout)
    return True
