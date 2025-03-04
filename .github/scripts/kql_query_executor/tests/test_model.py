import os
import re
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from model import CompressionType, KQLConfig, OutputConfig, OutputFormat, QueryConfig


def test_output_format_enum():
    """Test OutputFormat enumeration values."""
    assert OutputFormat.NONE == "none"
    assert OutputFormat.JSON == "json"
    assert OutputFormat.JSONC == "jsonc"
    assert OutputFormat.TABLE == "table"
    assert OutputFormat.TSV == "tsv"
    assert OutputFormat.YAML == "yaml"
    assert OutputFormat.YAMLC == "yamlc"


def test_output_format_extensions():
    """Test OutputFormat file extensions."""
    assert OutputFormat.NONE.extension() == ""
    assert OutputFormat.JSON.extension() == ".json"
    assert OutputFormat.JSONC.extension() == ".json"
    assert OutputFormat.TABLE.extension() == ".txt"
    assert OutputFormat.TSV.extension() == ".tsv"
    assert OutputFormat.YAML.extension() == ".yaml"
    assert OutputFormat.YAMLC.extension() == ".yaml"


def test_compression_type_enum():
    """Test CompressionType enumeration values."""
    assert CompressionType.GZIP == "gzip"
    assert CompressionType.ZIP == "zip"


def test_output_config_defaults():
    """Test OutputConfig default values."""
    config = OutputConfig(format=OutputFormat.JSON)
    assert config.format == OutputFormat.JSON
    assert config.query is None
    assert config.file is None
    assert config.compression is None


def test_output_config_with_query():
    """Test OutputConfig with JMESPath query."""
    config = OutputConfig(
        format=OutputFormat.JSON,
        query="[].{File: FileName, PID: ProcessId, Command: ProcessCommandLine}",
    )
    assert config.format == OutputFormat.JSON
    assert (
        config.query
        == "[].{File: FileName, PID: ProcessId, Command: ProcessCommandLine}"
    )


def test_output_config_with_file():
    """Test OutputConfig with file."""
    config = OutputConfig(
        format=OutputFormat.JSON,
        file="results/output.json",
    )
    assert config.format == OutputFormat.JSON
    assert config.file == "results/output.json"


def test_output_config_with_compression():
    """Test OutputConfig with compression."""
    config = OutputConfig(
        format=OutputFormat.JSON,
        file="results/output.json",
        compression=CompressionType.GZIP,
    )
    assert config.format == OutputFormat.JSON
    assert config.compression == CompressionType.GZIP


def test_output_config_whitespace_in_file():
    """Test that OutputConfig rejects files with whitespace."""
    expected_message = "Filename should not contain whitespace: 'output file.json'. Use underscores or dashes instead."
    with pytest.raises(ValueError, match=re.escape(expected_message)):
        OutputConfig(format=OutputFormat.JSON, file="output file.json")


def test_query_config_basic():
    """Test QueryConfig with basic properties."""
    config = QueryConfig(file="query.kql")
    assert config.file == "query.kql"
    assert config.output is None


def test_query_config_with_outputs():
    """Test QueryConfig with output configurations."""
    outputs = [
        OutputConfig(format=OutputFormat.JSON),
        OutputConfig(format=OutputFormat.YAML, file="results/output.yaml"),
    ]
    config = QueryConfig(file="query.kql", output=outputs)
    assert config.file == "query.kql"
    assert len(config.output) == 2
    assert config.output[0].format == OutputFormat.JSON
    assert config.output[1].format == OutputFormat.YAML
    assert config.output[1].file == "results/output.yaml"


def test_kql_config_defaults():
    """Test KQLConfig default values."""
    config = KQLConfig()
    assert config.version == "1.0"
    assert config.queries is None


def test_kql_config_with_queries():
    """Test KQLConfig with query configurations."""
    queries = [
        QueryConfig(file="query1.kql"),
        QueryConfig(file="query2.kql"),
    ]
    config = KQLConfig(version="1.0", queries=queries)
    assert config.version == "1.0"
    assert len(config.queries) == 2
    assert config.queries[0].file == "query1.kql"
    assert config.queries[1].file == "query2.kql"


def test_kql_config_invalid_query_extension():
    """Test KQLConfig validation for query file extension."""
    with pytest.raises(ValueError, match="Query file must end with .kql"):
        KQLConfig(version="1.0", queries=[QueryConfig(file="query.txt")])


def test_query_config_whitespace_in_file():
    """Test that QueryConfig rejects file paths with whitespace."""
    with pytest.raises(
        ValueError, match="Query file path should not contain whitespace"
    ):
        QueryConfig(file="query file.kql")


def test_query_config_valid_file_formats():
    """Test that QueryConfig accepts valid file paths."""
    # Underscore instead of space
    config1 = QueryConfig(file="query_file.kql")
    assert config1.file == "query_file.kql"

    # Nested path with underscores
    config2 = QueryConfig(file="my_folder/query.kql")
    assert config2.file == "my_folder/query.kql"

    # Dash instead of space
    config3 = QueryConfig(file="query-file.kql")
    assert config3.file == "query-file.kql"
