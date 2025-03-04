import logging
import os
import subprocess
import sys
from unittest import mock

import pytest

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execute import execute_query
from model import CompressionType, KQLConfig, OutputConfig, OutputFormat, QueryConfig


@pytest.fixture
def basic_config():
    """Basic configuration with a single query."""
    return KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="example.kql",
                output=[
                    OutputConfig(format=OutputFormat.JSONC),
                    OutputConfig(
                        format=OutputFormat.JSON,
                        file="query-results/output.json",
                        compression=CompressionType.GZIP,
                    ),
                ],
            )
        ],
    )


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_basic_execution_to_console(mock_get_configs, mock_subprocess_run, caplog):
    """Test basic execution with JSON output to console."""
    # Setup mocks
    mock_get_configs.return_value = [OutputConfig(format=OutputFormat.JSON)]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    mock_subprocess_run.assert_called_once()
    cmd = mock_subprocess_run.call_args[0][0]
    assert "--output" in cmd
    assert "json" in cmd
    assert "--query" not in cmd  # No JMESPath query


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
@mock.patch("os.makedirs")
@mock.patch("builtins.open", new_callable=mock.mock_open)
def test_output_to_file(
    mock_open, mock_makedirs, mock_get_configs, mock_subprocess_run
):
    """Test output to file with directory creation."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSON, file="results/output.json")
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    mock_makedirs.assert_called_once_with(
        os.path.dirname("results/output.json"), exist_ok=True
    )
    mock_open.assert_called_once_with("results/output.json", "w")
    mock_open().write.assert_called_once_with("test output")


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_format_none_skips_execution(mock_get_configs, mock_subprocess_run, caplog):
    """Test that NONE format skips execution."""
    # Configure caplog to capture the right log level
    caplog.set_level(logging.INFO)

    # Setup mocks
    mock_get_configs.return_value = [OutputConfig(format=OutputFormat.NONE)]

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    assert mock_subprocess_run.call_count == 0  # Should not execute any command
    assert "Skipping output for" in caplog.text


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_all_output_formats(mock_get_configs, mock_subprocess_run):
    """Test all available output formats."""
    formats = [
        OutputFormat.JSON,
        OutputFormat.JSONC,
        OutputFormat.TABLE,
        OutputFormat.TSV,
        OutputFormat.YAML,
        OutputFormat.YAMLC,
    ]

    # Execute each format
    for fmt in formats:
        # Reset mocks
        mock_subprocess_run.reset_mock()
        mock_get_configs.return_value = [OutputConfig(format=fmt)]
        mock_subprocess_run.return_value = mock.MagicMock(
            stdout=f"test {fmt.value} output", stderr="", returncode=0
        )

        # Execute query
        result = execute_query(
            folder_path="/test",
            file_path="query.kql",
            workspace_id="test-workspace",
            config=KQLConfig(),
        )

        # Verify
        assert result is True
        mock_subprocess_run.assert_called_once()
        cmd = mock_subprocess_run.call_args[0][0]
        assert "--output" in cmd
        assert fmt.value in cmd


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_jmespath_query(mock_get_configs, mock_subprocess_run):
    """Test JMESPath query parameters are correctly passed."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSON, query="length(@)")
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="5", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    cmd = mock_subprocess_run.call_args[0][0]
    assert "--query" in cmd
    assert "length(@)" in cmd


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_jmespath_error_handling(mock_get_configs, mock_subprocess_run, caplog):
    """Test handling of invalid JMESPath query."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSON, query="invalid[query")
    ]
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, "az monitor", stderr="JMESPath query failed: Invalid syntax at column 7"
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify failure
    assert result is False
    assert "Error executing query" in caplog.text
    assert "JMESPath query failed" in caplog.text


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
@mock.patch("os.makedirs")
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("gzip.open", new_callable=mock.mock_open)
@mock.patch("shutil.copyfileobj")
@mock.patch("os.remove")
def test_gzip_compression(
    mock_remove,
    mock_copyfileobj,
    mock_gzip_open,
    mock_open,
    mock_makedirs,
    mock_get_configs,
    mock_subprocess_run,
):
    """Test GZIP compression of output."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(
            format=OutputFormat.JSON,
            file="results/output.json",
            compression=CompressionType.GZIP,
        )
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True

    # Check the sequence of file operations including context manager calls
    expected_calls = [
        # Write the initial results
        mock.call("results/output.json", "w"),
        mock.call().__enter__(),
        mock.call().write("test output"),
        mock.call().__exit__(None, None, None),
        # Read for compression
        mock.call("results/output.json", "rb"),
        mock.call().__enter__(),
        mock.call().__exit__(None, None, None),
    ]
    mock_open.assert_has_calls(expected_calls, any_order=False)

    # Verify compression operations
    mock_gzip_open.assert_called_once_with("results/output.json.gz", "wb")
    mock_copyfileobj.assert_called_once()
    mock_remove.assert_called_once_with("results/output.json")


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
@mock.patch("os.makedirs")
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("shutil.make_archive")
@mock.patch("os.remove")
def test_zip_compression(
    mock_remove,
    mock_make_archive,
    mock_open,
    mock_makedirs,
    mock_get_configs,
    mock_subprocess_run,
):
    """Test ZIP compression of output."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(
            format=OutputFormat.JSON,
            file="results/output.json",
            compression=CompressionType.ZIP,
        )
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    mock_open.assert_called_once_with("results/output.json", "w")
    mock_make_archive.assert_called_once()
    assert "results/output" in mock_make_archive.call_args[0][0]  # base name
    assert "zip" in mock_make_archive.call_args[0][1]  # format
    mock_remove.assert_called_once_with("results/output.json")


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_multiple_formats(mock_get_configs, mock_subprocess_run):
    """Test execution with multiple output formats."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSONC),
        OutputConfig(
            format=OutputFormat.JSON,
            file="query-results/output.json",
            compression=CompressionType.GZIP,
        ),
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="example.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    assert mock_subprocess_run.call_count == 2  # Should call for each format

    # First call (JSONC to console)
    first_call = mock_subprocess_run.call_args_list[0]
    assert "--output" in first_call[0][0]
    assert "jsonc" in first_call[0][0]

    # Second call (JSON to file with compression)
    second_call = mock_subprocess_run.call_args_list[1]
    assert "--output" in second_call[0][0]
    assert "json" in second_call[0][0]


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_complex_filtering(mock_get_configs, mock_subprocess_run):
    """Test execution with multiple filtered outputs."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSONC),  # Console output in JSONC
        OutputConfig(
            format=OutputFormat.JSON,
            file="logs/security-events.json",
            compression=CompressionType.GZIP,
        ),  # Compressed file output
        OutputConfig(
            format=OutputFormat.JSON,
            query="events[?severity=='critical']",
            file="alerts/critical.json",
        ),  # Filtered by severity=critical
        OutputConfig(
            format=OutputFormat.JSON,
            query="events[?severity=='high']",
            file="alerts/high.json",
        ),  # Filtered by severity=high
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="security-events.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    assert mock_subprocess_run.call_count == 4  # Should call for each format

    # Check JMESPath queries were included correctly
    calls = mock_subprocess_run.call_args_list

    # No query for first two calls
    assert "--query" not in calls[0][0][0]
    assert "--query" not in calls[1][0][0]

    # Check filtered queries
    assert "--query" in calls[2][0][0]
    assert "events[?severity=='critical']" in calls[2][0][0]

    assert "--query" in calls[3][0][0]
    assert "events[?severity=='high']" in calls[3][0][0]


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_error_handling_query_execution(mock_get_configs, mock_subprocess_run, caplog):
    """Test handling of query execution errors."""
    # Setup mocks
    mock_get_configs.return_value = [OutputConfig(format=OutputFormat.JSON)]
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, "az monitor", stderr="Error: Invalid KQL query syntax at line 5"
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is False
    assert "Error executing query" in caplog.text
    assert "Error details: Error: Invalid KQL query syntax at line 5" in caplog.text


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
@mock.patch("os.makedirs")
def test_error_handling_file_operations(
    mock_makedirs, mock_get_configs, mock_subprocess_run, caplog
):
    """Test handling of file operation errors."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSON, file="results/output.json")
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )
    mock_makedirs.side_effect = PermissionError("Permission denied")

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is False
    assert "Unexpected error processing" in caplog.text
    assert "Permission denied" in caplog.text


@mock.patch("execute.get_output_configs_for_query")
def test_empty_configurations(mock_get_configs, caplog):
    """Test behavior with empty configurations."""
    # Configure caplog to capture the right log level
    caplog.set_level(logging.INFO)

    # Setup mocks to return empty list
    mock_get_configs.return_value = []

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="query.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True  # Should succeed even with no outputs
    assert "Executing /test/query.kql" in caplog.text


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_network_events_count(mock_get_configs, mock_subprocess_run):
    """Test example from docs: network events with count query."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSON, query="length(@)")
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="42", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="network-events.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    cmd = mock_subprocess_run.call_args[0][0]
    assert "--query" in cmd
    assert "length(@)" in cmd


### Examples from Configuration Guide ###
@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_example_basic_configuration(mock_get_configs, mock_subprocess_run):
    """Test the basic configuration example from documentation."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSONC),  # Console output
        OutputConfig(
            format=OutputFormat.JSON,
            file="query-results/output.json",
            compression=CompressionType.GZIP,
        ),  # File output with compression
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="example.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    assert mock_subprocess_run.call_count == 2

    # Check first call (JSONC to console)
    first_call = mock_subprocess_run.call_args_list[0]
    assert "--output" in first_call[0][0]
    assert "jsonc" in first_call[0][0]

    # Check second call (JSON to file with compression)
    second_call = mock_subprocess_run.call_args_list[1]
    assert "--output" in second_call[0][0]
    assert "json" in second_call[0][0]


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_example_multiple_queries(mock_get_configs, mock_subprocess_run):
    """Test the multiple queries example from documentation."""
    test_cases = [
        # device.kql with no output
        (
            "device.kql",
            [OutputConfig(format=OutputFormat.NONE)],
            0,  # Expected call count
        ),
        # user.kql with YAML output
        (
            "user.kql",
            [OutputConfig(format=OutputFormat.YAML)],
            1,  # Expected call count
        ),
        # network/nsg.kql with TSV output
        (
            "network/nsg.kql",
            [OutputConfig(format=OutputFormat.TSV)],
            1,  # Expected call count
        ),
        # network/vm.kql with table output
        (
            "network/vm.kql",
            [OutputConfig(format=OutputFormat.TABLE, file="subdir/vm.txt")],
            1,  # Expected call count
        ),
    ]

    for file_path, configs, expected_calls in test_cases:
        # Reset mocks
        mock_subprocess_run.reset_mock()
        mock_get_configs.return_value = configs
        mock_subprocess_run.return_value = mock.MagicMock(
            stdout="test output", stderr="", returncode=0
        )

        # Execute query
        result = execute_query(
            folder_path="/test",
            file_path=file_path,
            workspace_id="test-workspace",
            config=KQLConfig(),
        )

        # Verify
        assert result is True
        assert mock_subprocess_run.call_count == expected_calls

        # Check format-specific details
        if configs[0].format != OutputFormat.NONE:
            cmd = mock_subprocess_run.call_args[0][0]
            assert "--output" in cmd
            assert configs[0].format.value in cmd


@mock.patch("execute.subprocess.run")
@mock.patch("execute.get_output_configs_for_query")
def test_example_security_events_filtering(mock_get_configs, mock_subprocess_run):
    """Test the security events filtering example from documentation."""
    # Setup mocks
    mock_get_configs.return_value = [
        OutputConfig(format=OutputFormat.JSONC),
        OutputConfig(
            format=OutputFormat.JSON,
            file="logs/security-events.json",
            compression=CompressionType.GZIP,
        ),
        *[
            OutputConfig(
                format=OutputFormat.JSON,
                query=f"events[?severity=='{severity}']",
                file=f"alerts/{severity}.json",
            )
            for severity in ["critical", "high", "medium", "low"]
        ],
    ]
    mock_subprocess_run.return_value = mock.MagicMock(
        stdout="test output", stderr="", returncode=0
    )

    # Execute query
    result = execute_query(
        folder_path="/test",
        file_path="security-events.kql",
        workspace_id="test-workspace",
        config=KQLConfig(),
    )

    # Verify
    assert result is True
    assert (
        mock_subprocess_run.call_count == 6
    )  # 1 console + 1 compressed + 4 severity filters

    calls = mock_subprocess_run.call_args_list

    # Check format and queries for each call
    # First call: JSONC to console
    assert "jsonc" in calls[0][0][0]
    assert "--query" not in calls[0][0][0]

    # Second call: JSON with compression
    assert "json" in calls[1][0][0]
    assert "--query" not in calls[1][0][0]

    # Remaining calls: Severity-filtered outputs
    severities = ["critical", "high", "medium", "low"]
    for idx, severity in enumerate(severities, start=2):
        cmd = calls[idx][0][0]
        assert "json" in cmd
        assert "--query" in cmd
        assert f"events[?severity=='{severity}']" in cmd
