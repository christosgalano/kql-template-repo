#!/usr/bin/env python3

import argparse
import glob
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import yaml


# Enum definitions for better type safety
class OutputType(str, Enum):
    CONSOLE = "console"
    FILE = "file"


class CompressionType(str, Enum):
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"


# Dataclass definitions for configuration validation
@dataclass
class FormatConfig:
    type: OutputType
    query: str = "."
    path: str = field(default="query-results")
    filename_template: Optional[str] = None
    compression: CompressionType = CompressionType.NONE

    def __post_init__(self) -> None:
        # Validate path
        if self.type == OutputType.FILE and not self.path:
            raise ValueError("Path is required for file output type")

        # Validate filename_template if provided
        if self.filename_template:
            valid_placeholders = ["{query}", "{query-folder}"]
            found_placeholders = []

            for placeholder in valid_placeholders:
                if placeholder in self.filename_template:
                    found_placeholders.append(placeholder)

            if not found_placeholders:
                raise ValueError(
                    f"Filename template must contain at least one of: {', '.join(valid_placeholders)}"
                )


@dataclass
class OutputConfig:
    formats: List[FormatConfig]


@dataclass
class FilesConfig:
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.include and self.exclude:
            raise ValueError(
                "Cannot specify both include and exclude in files configuration"
            )


@dataclass
class KQLConfig:
    version: str = "1.0"
    files: Optional[FilesConfig] = None
    output: OutputConfig = field(
        default_factory=lambda: OutputConfig(
            formats=[FormatConfig(type=OutputType.CONSOLE)]
        )
    )


def setup_logging(log_level) -> None:
    """Configure logging with the specified level."""
    log_format = "%(message)s"
    if log_level == logging.DEBUG:
        log_format = "%(levelname)s: %(message)s"

    handlers = [logging.StreamHandler()]
    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)


def convert_dict_to_config(config_dict: Dict[str, Any]) -> KQLConfig:
    """Convert a dictionary to a KQLConfig object with validation."""
    try:
        # Process files section
        files_config = None
        if "files" in config_dict:
            files_dict = config_dict["files"]
            files_config = FilesConfig(
                include=files_dict.get("include"), exclude=files_dict.get("exclude")
            )

        # Process output section
        output_formats = []

        if "output" in config_dict:
            output_dict = config_dict["output"]
            if "formats" in output_dict:
                for fmt in output_dict["formats"]:
                    format_config = FormatConfig(
                        type=fmt["type"],
                        query=fmt.get("query", "."),
                        path=fmt.get(
                            "path",
                            "query-results"
                            if fmt["type"] == OutputType.FILE
                            else "stdout",
                        ),
                        filename_template=fmt.get("filename_template"),
                        compression=fmt.get("compression", CompressionType.NONE),
                    )
                    output_formats.append(format_config)

        if not output_formats:
            output_formats = [FormatConfig(type=OutputType.CONSOLE)]

        output_config = OutputConfig(formats=output_formats)

        return KQLConfig(
            version=config_dict.get("version", "1.0"),
            files=files_config,
            output=output_config,
        )
    except Exception as e:
        logging.error(f"Error converting configuration: {e}")
        sys.exit(1)


def load_config(config_path, schema_path=None) -> KQLConfig:
    """Load and validate the configuration file against schema."""
    try:
        with open(config_path, "r") as file:
            config_dict = yaml.safe_load(file) or {}

        if not schema_path:
            repo_root = Path(__file__).parent.parent.parent
            schema_path = repo_root / "kql-config-schema.json"
            if not schema_path.exists():
                logging.warning("Schema file not found, skipping validation")
            else:
                with open(schema_path, "r") as schema_file:
                    schema = json.load(schema_file)
                    jsonschema.validate(instance=config_dict, schema=schema)

        return convert_dict_to_config(config_dict)

    except jsonschema.exceptions.ValidationError as e:
        # This catches any validation errors not handled above
        logging.error(f"Config validation error: {e.message}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        sys.exit(1)


def find_config_file(folder_path) -> str | None:
    """Find the config file in the folder or repository root."""
    # First check in the specified folder
    for ext in ["yaml", "yml"]:
        config_file = os.path.join(folder_path, f".kql-config.{ext}")
        if os.path.exists(config_file):
            return config_file

    # If not found in folder, check repository root
    repo_root = Path(__file__).parent.parent.parent
    for ext in ["yaml", "yml"]:
        root_config_file = repo_root / f".kql-config.{ext}"
        if root_config_file.exists():
            logging.debug(f"Found config file in repository root: {root_config_file}")
            return str(root_config_file)

    return None


def get_applicable_files(folder_path, config: KQLConfig) -> list[str]:
    """Get list of applicable KQL files based on config."""
    all_files = [os.path.basename(f) for f in glob.glob(f"{folder_path}/*.kql")]

    if not config.files:
        return all_files

    if config.files.include:
        included_files = [f for f in config.files.include if f in all_files]
        if not included_files:
            logging.warning("None of the included files were found in the folder")
        return included_files

    if config.files.exclude:
        excluded_files = [f for f in all_files if f not in config.files.exclude]
        if not excluded_files:
            logging.warning("All files in folder were excluded")
        return excluded_files

    return all_files


def execute_query(
    folder_path, file_name, workspace_id, output_config: OutputConfig
) -> bool:
    """Execute a KQL query and process the results."""
    file_path = os.path.join(folder_path, file_name)
    temp_result_file = f"{file_path}.temp.json"

    logging.info(f"Executing {file_name}...")

    try:
        # Execute the KQL query using Azure CLI
        cmd = [
            "az",
            "monitor",
            "log-analytics",
            "query",
            "-w",
            workspace_id,
            "--analytics-query",
            f"@{file_path}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw_result = result.stdout.strip()

        # Save temporary raw results
        with open(temp_result_file, "w") as f:
            f.write(raw_result)

        # Get just the folder name without any prefix like "library/"
        query_folder = os.path.basename(folder_path)

        # Process each output format
        for fmt in output_config.formats:
            # Apply JQ filter if specified
            if fmt.query != ".":
                jq_cmd = ["jq", fmt.query, temp_result_file]
                jq_result = subprocess.run(
                    jq_cmd, capture_output=True, text=True, check=True
                )
                filtered_result = jq_result.stdout.strip()
            else:
                filtered_result = raw_result

            if fmt.type == OutputType.CONSOLE:
                logging.info(f"Results for {file_name}")
                print(filtered_result)
            elif fmt.type == OutputType.FILE:
                # Setup output directory based on path from config
                output_base = fmt.path

                # Use filename template if provided, otherwise use default template
                if fmt.filename_template:
                    filename = fmt.filename_template
                else:
                    # Default template: {query-folder}/{query}.json
                    filename = f"{query_folder}/{os.path.splitext(file_name)[0]}.json"

                # Replace placeholders
                filename = filename.replace("{query-folder}", query_folder)
                filename = filename.replace("{query}", os.path.splitext(file_name)[0])

                # Ensure output directory exists
                output_file = os.path.join(output_base, filename)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Write the results to file
                with open(output_file, "w") as f:
                    f.write(filtered_result)
                logging.info(f"Results saved to {output_file}")

                # Apply compression if specified
                if fmt.compression != CompressionType.NONE:
                    if fmt.compression == CompressionType.GZIP:
                        with (
                            open(output_file, "rb") as f_in,
                            gzip.open(output_file + ".gz", "wb") as f_out,
                        ):
                            shutil.copyfileobj(f_in, f_out)
                        os.remove(output_file)
                        logging.info(f"Compressed results with gzip: {output_file}.gz")
                    elif fmt.compression == CompressionType.ZIP:
                        zip_base = os.path.splitext(output_file)[0]
                        shutil.make_archive(
                            zip_base,
                            "zip",
                            root_dir=os.path.dirname(output_file),
                            base_dir=os.path.basename(output_file),
                        )
                        os.remove(output_file)
                        logging.info(f"Compressed results with zip: {zip_base}.zip")

        # Clean up temporary file
        if os.path.exists(temp_result_file):
            os.remove(temp_result_file)

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing query {file_name}: {e}")
        if hasattr(e, "stderr") and e.stderr:
            logging.error(
                f"Error details: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}"
            )
        return False
    except Exception as e:
        logging.error(f"Unexpected error processing {file_name}: {e}")
        return False


def create_config_from_args(args) -> KQLConfig:
    """Create a config object from command line arguments."""
    formats = []

    # Parse output formats
    if args.output_format == "both":
        formats.append(FormatConfig(type=OutputType.CONSOLE))
        formats.append(
            FormatConfig(
                type=OutputType.FILE,
                path=args.output_path,
                compression=args.compression
                if hasattr(args, "compression")
                else CompressionType.NONE,
            )
        )
    elif args.output_format == "file":
        formats.append(
            FormatConfig(
                type=OutputType.FILE,
                path=args.output_path,
                compression=args.compression
                if hasattr(args, "compression")
                else CompressionType.NONE,
            )
        )
    else:  # console is the default
        formats.append(FormatConfig(type=OutputType.CONSOLE))

    output_config = OutputConfig(formats=formats, query=args.query or ".")

    return KQLConfig(version="1.0", output=output_config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute KQL queries from a folder")
    parser.add_argument(
        "-f",
        "--folder",
        required=True,
        help="Path to the folder containing KQL files",
    )
    parser.add_argument(
        "-w", "--workspace-id", required=True, help="Azure Log Analytics workspace ID"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to the config file (default: look in folder then repo root)",
    )
    parser.add_argument(
        "-s",
        "--schema",
        help="Path to the schema file (default: kql-config-schema.json in repo root)",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="ERROR",
        help="Set logging level",
    )

    args = parser.parse_args()
    setup_logging(getattr(logging, args.log_level))

    folder_path = args.folder
    if not folder_path:
        parser.error("Folder path is required")

    if not os.path.isdir(folder_path):
        logging.error(f"Folder {folder_path} does not exist")
        sys.exit(1)

    # Load configuration
    config_path = args.config or find_config_file(folder_path)
    if config_path:
        logging.info(f"Using config file: {config_path}")
        config = load_config(config_path, args.schema)

        # Set default file output path to repo root
        repo_root = Path(__file__).parent.parent.parent
        default_output_path = str(repo_root / "query-results")

        # Update file output paths to default to repo root if relative
        for fmt in config.output.formats:
            if fmt.type == OutputType.FILE and not os.path.isabs(fmt.path):
                if fmt.path == "query-results":
                    fmt.path = default_output_path
    else:
        logging.info("No config file found, using default console output")
        # Create a minimal default config
        config = KQLConfig(
            output=OutputConfig(formats=[FormatConfig(type=OutputType.CONSOLE)])
        )

    applicable_files = get_applicable_files(folder_path, config)
    if not applicable_files:
        logging.info("No applicable KQL files found")
        sys.exit(0)

    logging.info(f"Found {len(applicable_files)} KQL file(s) to execute")

    success_count, fail_count = 0, 0
    for file_name in applicable_files:
        if execute_query(folder_path, file_name, args.workspace_id, config.output):
            success_count += 1
        else:
            fail_count += 1

    logging.info(f"Execution completed: {success_count} succeeded, {fail_count} failed")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
