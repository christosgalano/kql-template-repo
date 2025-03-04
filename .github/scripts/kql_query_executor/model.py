from dataclasses import dataclass
from enum import Enum


class OutputFormat(str, Enum):
    """
    Enumeration of supported output types for KQL query results.

    Attributes:
        NONE: No output
        JSON: JSON output
        JSONC: JSON output with colorization
        TABLE: Tabular output
        TSV: Tab-separated values
        YAML: YAML output
        YAMLC: YAML output with color
    """

    NONE = "none"
    JSON = "json"
    JSONC = "jsonc"
    TABLE = "table"
    TSV = "tsv"
    YAML = "yaml"
    YAMLC = "yamlc"

    def extension(self) -> str:
        """Returns the file extension for the output format."""
        return {
            OutputFormat.NONE: "",
            OutputFormat.JSON: ".json",
            OutputFormat.JSONC: ".json",
            OutputFormat.TABLE: ".txt",
            OutputFormat.TSV: ".tsv",
            OutputFormat.YAML: ".yaml",
            OutputFormat.YAMLC: ".yaml",
        }.get(self, "")


class CompressionType(str, Enum):
    """
    Enumeration of supported compression formats for file outputs.

    Attributes:
        GZIP: GZip compression (.gz)
        ZIP: Zip archive (.zip)
    """

    GZIP = "gzip"
    ZIP = "zip"


@dataclass
class OutputConfig:
    """
    Configuration for an individual output format.

    Attributes:
        format: Output destination type (console or file)
        query: JMESPath query string to apply. See http://jmespath.org/ for more information and examples.
        file: Output file. If not specified, print to stdout.
        compression: Compression format for file outputs.
    """

    format: OutputFormat
    query: str | None = None
    file: str | None = None
    compression: CompressionType | None = None

    def __post_init__(self) -> None:
        # Reject whitespace in filenames
        if self.file and any(c.isspace() for c in self.file):
            raise ValueError(
                f"Filename should not contain whitespace: '{self.file}'. "
                f"Use underscores or dashes instead."
            )


@dataclass
class QueryConfig:
    """
    Configuration for an individual KQL query.

    Attributes:
        file: Path to the KQL file containing the query
        output: Query-specific output configurations (overrides defaults)
    """

    file: str
    output: list[OutputConfig] | None = None

    def __post_init__(self) -> None:
        # Verify file ends with ".kql"
        if not self.file.endswith(".kql"):
            raise ValueError(f"Query file must end with .kql: {self.file}")

        # Check for whitespace in file path
        if any(c.isspace() for c in self.file):
            raise ValueError(
                f"Query file path should not contain whitespace: '{self.file}'. "
                f"Use underscores or dashes instead."
            )


@dataclass
class KQLConfig:
    """
    Root configuration for KQL query execution.

    Attributes:
        version: Schema version string
        queries: List of specific query configurations
    """

    version: str = "1.0"
    queries: list[QueryConfig] = None
