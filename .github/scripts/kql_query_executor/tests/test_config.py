import os
import sys
import tempfile
from unittest import mock

import pytest
import yaml

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    convert_dict_to_config,
    find_config_file,
    get_applicable_files,
    get_output_configs_for_query,
    load_config,
    validate_file_path,
)
from model import CompressionType, KQLConfig, OutputConfig, OutputFormat, QueryConfig


@pytest.fixture
def temp_dir_with_files():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a KQL file
        kql_file = os.path.join(temp_dir, "test_query.kql")
        with open(kql_file, "w") as f:
            f.write("// Test KQL query\nTable | take 10")

        # Create a non-KQL file
        txt_file = os.path.join(temp_dir, "test_file.txt")
        with open(txt_file, "w") as f:
            f.write("This is not a KQL file")

        # Create a subdirectory with another KQL file
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        sub_kql_file = os.path.join(subdir, "subdir_query.kql")
        with open(sub_kql_file, "w") as f:
            f.write("// Subdirectory KQL query\nTable | where Column == 'value'")

        yield temp_dir


@pytest.fixture
def basic_config_dict():
    """Return a basic configuration dictionary."""
    return {
        "version": "1.0",
        "queries": [
            {
                "file": "test_query.kql",
                "output": [{"format": "json"}],
            }
        ],
    }


@pytest.fixture
def complex_config_dict():
    """Return a complex configuration dictionary with multiple outputs and compression."""
    return {
        "version": "1.0",
        "queries": [
            {
                "file": "test_query.kql",
                "output": [
                    {"format": "json", "query": "[].{Name: name, Count: count}"},
                    {"format": "json", "file": "results/test_output.json"},
                    {
                        "format": "json",
                        "file": "compressed_results/compressed_output.json",
                        "compression": "gzip",
                    },
                ],
            },
            {
                "file": "subdir/subdir_query.kql",
                "output": [{"format": "yaml", "file": "subdir_results/output.yaml"}],
            },
        ],
    }


def test_find_config_file_in_folder(temp_dir_with_files):
    """Test finding a config file in the specified folder."""
    # Create config file in the temp directory
    config_path = os.path.join(temp_dir_with_files, ".kql-config.yaml")
    with open(config_path, "w") as f:
        f.write("version: '1.0'")

    # Test finding the config file
    found_path = find_config_file(temp_dir_with_files)
    assert found_path == config_path


def test_find_config_file_yml_extension(temp_dir_with_files):
    """Test finding a config file with .yml extension."""
    # Create config file with .yml extension
    config_path = os.path.join(temp_dir_with_files, ".kql-config.yml")
    with open(config_path, "w") as f:
        f.write("version: '1.0'")

    # Test finding the config file
    found_path = find_config_file(temp_dir_with_files)
    assert found_path == config_path


@mock.patch("config.Path")
def test_find_config_file_not_found(mock_path, temp_dir_with_files):
    """Test behavior when config file is not found."""
    # Mock repo_root path to ensure it doesn't find a real config file
    mock_repo_root = mock.MagicMock()
    mock_path.return_value.parent.parent.parent.parent = mock_repo_root
    mock_repo_root.__truediv__.return_value.exists.return_value = False

    # No config file created
    found_path = find_config_file(temp_dir_with_files)
    assert found_path is None


def test_validate_file_path_valid(temp_dir_with_files):
    """Test validating a valid KQL file path."""
    file_path = "test_query.kql"
    result = validate_file_path(file_path, temp_dir_with_files)
    assert result == file_path


def test_validate_file_path_not_kql(temp_dir_with_files):
    """Test validating a file path that doesn't end with .kql."""
    file_path = "test_file.txt"
    with pytest.raises(ValueError, match="Query file must end with .kql"):
        validate_file_path(file_path, temp_dir_with_files)


def test_validate_file_path_not_exist(temp_dir_with_files):
    """Test validating a file path that doesn't exist."""
    file_path = "nonexistent.kql"
    with pytest.raises(ValueError, match="Query file does not exist"):
        validate_file_path(file_path, temp_dir_with_files)


def test_validate_file_path_in_subdir(temp_dir_with_files):
    """Test validating a file path in a subdirectory."""
    file_path = "subdir/subdir_query.kql"
    result = validate_file_path(file_path, temp_dir_with_files)
    assert result == file_path


def test_convert_dict_to_config_invalid_file(temp_dir_with_files):
    """Test that files with invalid characters raise an exception."""
    # Create config with invalid file path
    invalid_config = {
        "version": "1.0",
        "queries": [
            {
                "file": "test_query.kql",
                "output": [
                    {
                        "format": "json",
                        "file": "invalid/ path/file.json",  # Contains whitespace
                    }
                ],
            }
        ],
    }

    # We expect this to raise a ValueError, but it's caught inside convert_dict_to_config
    # and converted to a SystemExit exception.
    with pytest.raises(SystemExit):
        convert_dict_to_config(invalid_config, temp_dir_with_files)


def test_convert_dict_to_config_basic(temp_dir_with_files, basic_config_dict):
    """Test converting a basic config dictionary to a KQLConfig object."""
    config = convert_dict_to_config(basic_config_dict, temp_dir_with_files)

    assert config.version == "1.0"
    assert len(config.queries) == 1
    assert config.queries[0].file == "test_query.kql"
    assert config.queries[0].output[0].format == OutputFormat.JSON


def test_convert_dict_to_config_complex(temp_dir_with_files, complex_config_dict):
    """Test converting a complex config dictionary to a KQLConfig object."""
    config = convert_dict_to_config(complex_config_dict, temp_dir_with_files)

    assert config.version == "1.0"
    assert len(config.queries) == 2

    # First query checks
    query1 = config.queries[0]
    assert query1.file == "test_query.kql"
    assert len(query1.output) == 3

    # Check JMESPath query output
    assert query1.output[0].format == OutputFormat.JSON
    assert query1.output[0].query == "[].{Name: name, Count: count}"

    # Check file output without compression
    assert query1.output[1].format == OutputFormat.JSON
    assert query1.output[1].file == "results/test_output.json"

    # Check file output with compression
    assert query1.output[2].format == OutputFormat.JSON
    assert query1.output[2].file == "compressed_results/compressed_output.json"
    assert query1.output[2].compression == CompressionType.GZIP

    # Second query checks
    query2 = config.queries[1]
    assert query2.file == "subdir/subdir_query.kql"
    assert len(query2.output) == 1
    assert query2.output[0].format == OutputFormat.YAML
    assert query2.output[0].file == "subdir_results/output.yaml"


def test_convert_dict_to_config_empty():
    """Test converting an empty config dictionary."""
    config = convert_dict_to_config({}, "/tmp")

    assert config.version == "1.0"
    assert config.queries == []


@mock.patch("config.jsonschema.validate")
def test_load_config_valid(mock_validate, temp_dir_with_files, basic_config_dict):
    """Test loading a valid configuration file."""
    # Create a valid config file
    config_path = os.path.join(temp_dir_with_files, ".kql-config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(basic_config_dict, f)

    # Create a mock schema file
    schema_path = os.path.join(temp_dir_with_files, "schema.json")
    with open(schema_path, "w") as f:
        f.write('{"type":"object"}')

    # Load the config
    config = load_config(config_path, schema_path)

    # Verify the config was loaded correctly
    assert isinstance(config, KQLConfig)
    assert config.version == "1.0"
    assert len(config.queries) == 1
    assert config.queries[0].file == "test_query.kql"


@mock.patch("config.sys.exit")
def test_load_config_validation_error(mock_exit, temp_dir_with_files):
    """Test loading a config that fails schema validation."""
    # Create an invalid config file (missing required 'file' field)
    config_path = os.path.join(temp_dir_with_files, "invalid_config.yaml")
    with open(config_path, "w") as f:
        f.write(
            """
        version: '1.0'
        queries:
          - output:
            - format: json
        """
        )

    # Define a mock schema that requires 'file' field
    schema_path = os.path.join(temp_dir_with_files, "schema.json")
    with open(schema_path, "w") as f:
        f.write(
            """
        {
          "type": "object",
          "properties": {
            "queries": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["file"]
              }
            }
          }
        }
        """
        )

    # This should fail validation and exit
    load_config(config_path, schema_path)

    # Verify sys.exit was called
    mock_exit.assert_called_once()


@mock.patch("config.sys.exit")
def test_load_config_file_not_found(mock_exit):
    """Test loading a config file that doesn't exist."""
    load_config("nonexistent_file.yaml")

    # Verify sys.exit was called
    mock_exit.assert_called_once()


def test_get_applicable_files_no_config(temp_dir_with_files):
    """Test getting applicable files when no queries are configured."""
    # Create empty config
    config = KQLConfig(version="1.0", queries=[])

    # Get applicable files
    files = get_applicable_files(temp_dir_with_files, config)

    # Should return all KQL files in the directory and subdirectories
    assert len(files) == 2
    assert "test_query.kql" in files
    assert "subdir/subdir_query.kql" in files


def test_get_applicable_files_with_config(temp_dir_with_files):
    """Test getting applicable files from configuration."""
    # Create config with specific queries
    config = KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="test_query.kql", output=[OutputConfig(format=OutputFormat.JSON)]
            )
        ],
    )

    # Get applicable files
    files = get_applicable_files(temp_dir_with_files, config)

    # Should return only the specified file
    assert len(files) == 1
    assert "test_query.kql" in files


def test_get_applicable_files_with_subdir_config(temp_dir_with_files):
    """Test getting applicable files with subdirectory paths."""
    # Create config with file in subdirectory
    config = KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="subdir/subdir_query.kql",
                output=[OutputConfig(format=OutputFormat.JSON)],
            )
        ],
    )

    # Get applicable files
    files = get_applicable_files(temp_dir_with_files, config)

    # Should return only the specified file
    assert len(files) == 1
    assert "subdir/subdir_query.kql" in files


def test_get_applicable_files_invalid_path(temp_dir_with_files):
    """Test getting applicable files with an invalid path in config."""
    # Create config with invalid file path
    config = KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="nonexistent.kql", output=[OutputConfig(format=OutputFormat.JSON)]
            )
        ],
    )

    # Get applicable files
    files = get_applicable_files(temp_dir_with_files, config)

    # Should return empty list since the path is invalid
    assert len(files) == 0


def test_get_applicable_files_multiple_subdirs(temp_dir_with_files):
    """Test getting applicable files from multiple nested subdirectories."""
    # Create multiple nested subdirectories with KQL files
    nested_dir1 = os.path.join(temp_dir_with_files, "logs")
    os.makedirs(nested_dir1)
    nested_kql1 = os.path.join(nested_dir1, "logs_query.kql")
    with open(nested_kql1, "w") as f:
        f.write("// Logs KQL query\nLogs | where Level == 'Error'")

    nested_dir2 = os.path.join(temp_dir_with_files, "metrics", "system")
    os.makedirs(nested_dir2)
    nested_kql2 = os.path.join(nested_dir2, "cpu_usage.kql")
    with open(nested_kql2, "w") as f:
        f.write("// CPU usage query\nPerf | where CounterName == 'CPU'")

    nested_dir3 = os.path.join(temp_dir_with_files, "metrics", "network")
    os.makedirs(nested_dir3)
    nested_kql3 = os.path.join(nested_dir3, "network_traffic.kql")
    with open(nested_kql3, "w") as f:
        f.write("// Network traffic query\nPerf | where CounterName == 'Network'")

    # Create empty config (no specific queries)
    config = KQLConfig(version="1.0", queries=[])

    # Get applicable files
    files = get_applicable_files(temp_dir_with_files, config)

    # Should find all KQL files in all subdirectories
    assert len(files) == 5  # 2 original + 3 new

    # Original files
    assert "test_query.kql" in files
    assert "subdir/subdir_query.kql" in files

    # Files in new subdirectories
    assert "logs/logs_query.kql" in files
    assert "metrics/system/cpu_usage.kql" in files
    assert "metrics/network/network_traffic.kql" in files


def test_get_output_configs_for_query(temp_dir_with_files):
    """Test getting output configs for a specific query."""
    config = KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="test_query.kql",
                output=[
                    OutputConfig(
                        format=OutputFormat.JSON, query="[].{Name: name, Count: count}"
                    )
                ],
            ),
            QueryConfig(
                file="subdir/subdir_query.kql",
                output=[
                    OutputConfig(
                        format=OutputFormat.YAML, file="custom_dir/output.yaml"
                    )
                ],
            ),
        ],
    )

    # Get output config for the first query
    configs1 = get_output_configs_for_query(config, "test_query.kql")
    assert len(configs1) == 1
    assert configs1[0].format == OutputFormat.JSON
    assert configs1[0].query == "[].{Name: name, Count: count}"

    # Get output config for the second query
    configs2 = get_output_configs_for_query(config, "subdir_query.kql")
    assert len(configs2) == 1
    assert configs2[0].format == OutputFormat.YAML
    assert configs2[0].file == "custom_dir/output.yaml"


def test_get_output_configs_default(temp_dir_with_files):
    """Test getting default output config when no matching query found."""
    config = KQLConfig(
        version="1.0",
        queries=[
            QueryConfig(
                file="different.kql",
                output=[
                    OutputConfig(format=OutputFormat.YAML, file="results/output.yaml")
                ],
            )
        ],
    )

    # Get output config for a query not in the config
    configs = get_output_configs_for_query(config, "test_query.kql")

    # Should get default JSON output
    assert len(configs) == 1
    assert configs[0].format == OutputFormat.JSON
