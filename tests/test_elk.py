# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

import pytest

from capellambse_context_diagrams._elkjs import (
    ELKInputData,
    ELKManager,
    ELKOutputData,
)


def test_binary_name_resolution():
    manager = ELKManager()
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch("platform.machine", return_value="x86_64"),
        mock.patch("importlib.metadata.version", return_value="1.0.0"),
    ):
        assert manager.binary_name == "elk-v1.0.0-x86_64-unknown-linux-gnu"


def test_binary_name_resolution_windows():
    manager = ELKManager()
    with (
        mock.patch("platform.system", return_value="Windows"),
        mock.patch("platform.machine", return_value="AMD64"),
        mock.patch("importlib.metadata.version", return_value="1.0.0"),
    ):
        assert manager.binary_name == "elk-v1.0.0-x86_64-pc-windows-msvc.exe"


def test_unsupported_platform():
    manager = ELKManager()
    with (
        mock.patch("platform.system", return_value="SolarOS"),
        mock.patch("platform.machine", return_value="SPARC"),
        pytest.raises(RuntimeError, match="Unsupported platform"),
    ):
        _ = manager.binary_name


@mock.patch("requests.get")
def test_download_binary(mock_get):
    manager = ELKManager()
    mock_response = mock.Mock()
    mock_response.content = b"binary content"
    mock_get.return_value = mock_response

    mock_stat = mock.Mock()
    mock_stat.st_mode = 0o644  # Typical default file permissions

    with (
        mock.patch("pathlib.Path.exists", return_value=False),
        mock.patch("pathlib.Path.mkdir"),
        mock.patch("builtins.open", mock.mock_open()),
        mock.patch("pathlib.Path.chmod"),
        mock.patch("pathlib.Path.stat", return_value=mock_stat),
        mock.patch(
            "platformdirs.user_cache_dir", return_value="/mock/cache/dir"
        ),
        mock.patch(
            "capellambse_context_diagrams._elkjs.ELKManager.binary_name",
            new_callable=mock.PropertyMock,
            return_value="mock-binary",
        ),
    ):
        manager.download_binary()
        mock_get.assert_called_once()


def test_process_management():
    manager = ELKManager()

    # Mock successful process startup
    mock_process = mock.Mock()
    mock_process.stdout.readline.return_value = (
        "--- ELK layouter started ---\n"
    )

    with mock.patch("subprocess.Popen", return_value=mock_process):
        manager._spawn_process_deno()
        assert manager._proc is not None

        # Test process termination
        manager.terminate_process()
        mock_process.terminate.assert_called_once()
        assert manager._proc is None


def test_call_elkjs():
    manager = ELKManager()

    # Mock process interaction
    mock_process = mock.Mock()
    mock_process.stdout.readline.side_effect = [
        "--- ELK layouter started ---\n",
        '{"id": "root", "type": "graph", "children": []}\n',
    ]

    with mock.patch("subprocess.Popen", return_value=mock_process):
        manager.spawn_process()

        # Test layout calculation
        input_model = ELKInputData(id="root")
        result = manager.call_elkjs(input_model)

        assert isinstance(result, ELKOutputData)
        assert result.id == "root"
        assert result.type == "graph"
        assert result.children == []


def test_failed_process_start():
    manager = ELKManager()

    # Mock failed process startup
    mock_process = mock.Mock()
    mock_process.stdout.readline.return_value = "Error starting ELK\n"

    with (
        mock.patch("subprocess.Popen", return_value=mock_process),
        pytest.raises(
            RuntimeError, match="Failed to start elk.js helper process"
        ),
    ):
        manager._spawn_process_deno()


def test_auto_spawn_on_call():
    manager = ELKManager()

    # Mock successful process startup
    mock_process = mock.Mock()
    mock_process.stdout.readline.side_effect = [
        "--- ELK layouter started ---\n",
        '{"id": "root", "type": "graph", "children": []}\n',
    ]

    with mock.patch("subprocess.Popen", return_value=mock_process):
        # Process should be started automatically when needed
        input_model = ELKInputData(id="root")
        result = manager.call_elkjs(input_model)

        assert isinstance(result, ELKOutputData)
        assert manager._proc is not None


def test_spawn_process_preference_order():
    manager = ELKManager()
    mock_process = mock.Mock()
    mock_process.stdout.readline.return_value = (
        "--- ELK layouter started ---\n"
    )

    # Prefer existing binary
    with (
        mock.patch("pathlib.Path.exists", return_value=True),
        mock.patch("subprocess.Popen", return_value=mock_process),
        mock.patch.object(manager, "_spawn_process_binary") as mock_binary,
        mock.patch.object(manager, "_spawn_process_deno") as mock_deno,
    ):
        manager.spawn_process()
        mock_binary.assert_called_once()
        mock_deno.assert_not_called()

    # Use deno if binary doesn't exist but deno is available
    with (
        mock.patch("pathlib.Path.exists", return_value=False),
        mock.patch("shutil.which", return_value="/usr/bin/deno"),
        mock.patch("subprocess.Popen", return_value=mock_process),
        mock.patch.object(manager, "_spawn_process_binary") as mock_binary,
        mock.patch.object(manager, "_spawn_process_deno") as mock_deno,
    ):
        manager.spawn_process()
        mock_deno.assert_called_once()
        mock_binary.assert_not_called()

    # Download and use binary if neither exists
    with (
        mock.patch("pathlib.Path.exists", return_value=False),
        mock.patch("shutil.which", return_value=None),
        mock.patch("subprocess.Popen", return_value=mock_process),
        mock.patch.object(manager, "_spawn_process_binary") as mock_binary,
        mock.patch.object(manager, "_spawn_process_deno") as mock_deno,
    ):
        manager.spawn_process()
        mock_binary.assert_called_once()
        mock_deno.assert_not_called()
