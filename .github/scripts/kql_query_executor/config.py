import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from model import (
    CompressionType,
    KQLConfig,
    OutputConfig,
    OutputFormat,
    QueryConfig,
)


def find_config_file(folder_path: str) -> str | None:
    """Find the config file in the folder or repository root."""
    # First check in the specified folder
    for ext in ["yaml", "yml"]:
        config_file = os.path.join(folder_path, f".kql-config.{ext}")
        if os.path.exists(config_file):
            return config_file

    # If not found in folder, check repository root
    repo_root = Path(__file__).parent.parent.parent.parent
    for ext in ["yaml", "yml"]:
        root_config_file = repo_root / f".kql-config.{ext}"
        if root_config_file.exists():
            logging.debug(f"Found config file in repository root: {root_config_file}")
            return str(root_config_file)

    return None


def validate_file_path(file_path: str, config_dir: str) -> str:
    """Validate that a query file exists and ends with .kql."""
    if not file_path.endswith(".kql"):
        raise ValueError(f"Query file must end with .kql: {file_path}")

    # Handle relative paths from config file location
    abs_path = os.path.normpath(os.path.join(config_dir, file_path))
    if not os.path.isfile(abs_path):
        raise ValueError(
            f"Query file does not exist: {file_path} (resolved to {abs_path})"
        )

    return file_path


def convert_dict_to_config(config_dict: dict[str, Any], config_dir: str) -> KQLConfig:
    """Convert a dictionary to a KQLConfig object with validation."""
    try:
        # Process queries section
        queries = []
        if "queries" in config_dict:
            for query_dict in config_dict["queries"]:
                validate_file_path(query_dict["file"], config_dir)

                query_output = None
                if "output" in query_dict:
                    query_output = []
                    for fmt in query_dict["output"]:
                        # Parse output format
                        format_str = fmt["format"]
                        try:
                            output_format = OutputFormat(format_str)
                        except ValueError:
                            raise ValueError(f"Invalid output format: {format_str}")

                        # Handle output file based on format
                        output_file = fmt.get("file")
                        if output_file and output_format != OutputFormat.NONE:
                            # Verify file path doesn't contain whitespace
                            if any(c.isspace() for c in output_file):
                                raise ValueError(
                                    f"Output file path should not contain whitespace: '{output_file}'. "
                                    f"Use underscores or dashes instead."
                                )

                            # Check if file exists (will be overwritten)
                            abs_file_path = os.path.normpath(
                                os.path.join(config_dir, output_file)
                            )
                            if os.path.exists(abs_file_path):
                                logging.warning(
                                    f"Output file exists and will be overwritten: {output_file}"
                                )

                            # Ensure directory exists
                            dir_path = os.path.dirname(abs_file_path)
                            if not os.path.exists(dir_path):
                                logging.info(
                                    f"Directory does not exist and will be created: {dir_path}"
                                )

                        # Handle compression
                        compression_str = fmt.get("compression")
                        compression = None
                        if compression_str:
                            try:
                                compression = CompressionType(compression_str)
                            except ValueError:
                                raise ValueError(
                                    f"Invalid compression type: {compression_str}"
                                )

                        # Create output config
                        format_config = OutputConfig(
                            format=output_format,
                            query=fmt.get("query"),  # JMESPath query
                            file=output_file,  # Full file path if specified
                            compression=compression,
                        )
                        query_output.append(format_config)

                query_config = QueryConfig(
                    file=query_dict["file"],
                    output=query_output,
                )
                queries.append(query_config)

        return KQLConfig(
            version=config_dict.get("version", "1.0"),
            queries=queries,
        )
    except Exception as e:
        logging.error(f"Error converting configuration: {e}")
        sys.exit(1)


def load_config(config_path: str, schema_path: str | None = None) -> KQLConfig:
    """Load and validate the configuration file against schema."""
    try:
        # Try to load YAML config
        try:
            with open(config_path, "r") as file:
                config_dict = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            logging.error(f"Invalid YAML format in {config_path}: {str(e)}")
            sys.exit(1)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)

        # Handle schema validation
        if not schema_path:
            repo_root = Path(__file__).parent.parent.parent.parent
            schema_path = str(repo_root / "kql-config-schema.json")

        if not os.path.exists(schema_path):
            logging.warning(
                f"Schema file not found at {schema_path}, skipping validation"
            )
        else:
            try:
                with open(schema_path, "r") as schema_file:
                    schema = json.load(schema_file)
                jsonschema.validate(instance=config_dict, schema=schema)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON schema file {schema_path}: {str(e)}")
                sys.exit(1)
            except jsonschema.exceptions.ValidationError as e:
                # Provide more detailed validation error message
                logging.error(
                    f"Config validation failed for {config_path}: {e.message}\n"
                )
                sys.exit(1)

        # Convert config dictionary to object
        config_dir = os.path.dirname(os.path.abspath(config_path))
        try:
            return convert_dict_to_config(config_dict, config_dir)
        except ValueError as e:
            logging.error(f"Invalid configuration value: {str(e)}")
            sys.exit(1)
        except KeyError as e:
            logging.error(f"Missing required configuration key: {str(e)}")
            sys.exit(1)

    except Exception as e:
        # Catch-all for unexpected errors with more context
        logging.error(
            f"Unexpected error loading config {config_path}:\n"
            f"  Type: {type(e).__name__}\n"
            f"  Error: {str(e)}"
        )
        sys.exit(1)


def get_applicable_files(folder_path: str, config: KQLConfig) -> list[str]:
    """Get list of applicable KQL files based on config."""
    # If no queries are configured, find all KQL files in the folder and subfolders
    if not config.queries:
        all_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".kql"):
                    # Get path relative to the specified folder
                    rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                    all_files.append(rel_path)
        return all_files

    # If queries are configured, use only those files
    config_files = []

    # The folder_path is used as the base for relative paths
    # We don't need to get parent directory which causes the "../" prefix issue

    for query in config.queries:
        file_path = query.file
        try:
            # Check if the file exists in the folder or a subdirectory
            # First try as relative to folder_path
            full_path = os.path.join(folder_path, file_path)

            if os.path.isfile(full_path):
                # File exists, use the relative path directly
                config_files.append(file_path)
            else:
                # File doesn't exist, log warning and skip
                logging.warning(f"Query file does not exist: {file_path}")
                # Don't add to config_files
        except Exception as e:
            logging.warning(f"Skipping invalid query file {file_path}: {e}")
            continue

    if not config_files:
        logging.warning("No valid query files found in configuration")

    return config_files


def get_output_configs_for_query(config: KQLConfig, file: str) -> list[OutputConfig]:
    """Determine which output configs to use for a query."""
    # Get the base name without extension
    file_path_variations = [
        file,  # Just the file name
        os.path.join("*", file),  # Any subfolder/file name
        f"**/{file}",  # Any nested path to file name
    ]

    # Check if there's a specific query configuration
    if config.queries:
        for query in config.queries:
            # Check if this config applies to our file
            # Match by either exact path or filename
            query_file = query.file
            file_basename = os.path.basename(query_file)

            if file == file_basename or any(
                file_pattern in query_file for file_pattern in file_path_variations
            ):
                if query.output:
                    logging.debug(f"Found specific output config for {file}")
                    return query.output

    # If no specific configuration found, use default JSON output to console
    logging.debug(f"Using default JSON output for {file}")
    return [OutputConfig(format=OutputFormat.JSON)]
