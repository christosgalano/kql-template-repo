#!/usr/bin/env python3
# filepath: /Users/galano/Developer/christos/cloud/azure/kql-repository/.github/scripts/execute_queries.py

import argparse
import glob
import os
import subprocess
import sys

import yaml


def load_config(config_path):
    """Load and validate the configuration file."""
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file) or {}

        # Set defaults if not provided
        if "version" not in config:
            config["version"] = "1.0"

        if "output" not in config:
            config["output"] = {"format": "console", "query": "."}
        elif "format" not in config["output"]:
            config["output"]["format"] = "console"
        elif "query" not in config["output"]:
            config["output"]["query"] = "."

        # Validation
        if config["version"] != "1.0":
            print("Error: Unsupported version")
            sys.exit(1)

        # Validate files section
        if "files" in config:
            if "include" in config["files"] and "exclude" in config["files"]:
                print("Error: Both include and exclude can't be specified")
                sys.exit(1)

        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def find_config_file(folder_path) -> str | None:
    """Find the config file in the folder (.kql-config.yaml or .kql-config.yml)."""
    config_files = [
        os.path.join(folder_path, ".kql-config.yaml"),
        os.path.join(folder_path, ".kql-config.yml"),
    ]

    for config_file in config_files:
        if os.path.exists(config_file):
            return config_file

    return None


def get_applicable_files(folder_path, config) -> list[str]:
    """Get list of applicable KQL files based on config."""
    all_files = [os.path.basename(f) for f in glob.glob(f"{folder_path}/*.kql")]

    if "files" not in config:
        return all_files

    if "include" in config["files"] and config["files"]["include"]:
        return [f for f in config["files"]["include"] if f in all_files]

    if "exclude" in config["files"] and config["files"]["exclude"]:
        return [f for f in all_files if f not in config["files"]["exclude"]]

    return all_files


def execute_query(folder_path, file_name, workspace_id, output_config) -> bool:
    """Execute a KQL query and process the results."""
    file_path = os.path.join(folder_path, file_name)
    result_file = f"{file_path}.json"

    print(f"Executing {file_name}...")

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

        with open(result_file, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, stderr=subprocess.PIPE, check=True)

        # Process output with jq
        jq_query = output_config.get("query", ".")
        jq_cmd = ["jq", jq_query, result_file]

        jq_result = subprocess.run(jq_cmd, capture_output=True, text=True, check=True)

        # Handle output format
        output_format = output_config.get("format", "console")
        if output_format == "console":
            print(f"Number of results for {file_name}: {jq_result.stdout.strip()}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing query {file_name}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute KQL queries from a folder")
    parser.add_argument("folder", help="Path to the folder containing KQL files")
    parser.add_argument(
        "-w", "--workspace-id", required=True, help="Azure Log Analytics workspace ID"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to the config file (defaults to .kql-config.yaml in the folder)",
    )
    parser.add_argument(
        "-o",
        "--output-format",
        choices=["console"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "-q",
        "--query",
        default="length",
        help="JQ query to run on results (default: length)",
    )

    args = parser.parse_args()

    folder_path = args.folder
    workspace_id = args.workspace_id

    # Check if folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        sys.exit(1)

    # Determine config file path
    config_path = args.config
    if not config_path:
        config_path = find_config_file(folder_path)

    # Load config or use CLI args
    if config_path:
        print(f"Using config file: {config_path}")
        config = load_config(config_path)
    else:
        print("No config file found. Using command line arguments.")
        config = {"output": {"format": args.output_format, "query": args.query}}

    # Override config with CLI args if provided
    if args.output_format:
        config["output"]["format"] = args.output_format
    if args.query:
        config["output"]["query"] = args.query

    # Get applicable files
    applicable_files = get_applicable_files(folder_path, config)

    if not applicable_files:
        print("No applicable KQL files found")
        sys.exit(0)

    print(
        f"Found {len(applicable_files)} applicable files: {', '.join(applicable_files)}"
    )

    # Process each file
    success_count = 0
    fail_count = 0

    for file_name in applicable_files:
        success = execute_query(folder_path, file_name, workspace_id, config["output"])
        if success:
            success_count += 1
        else:
            fail_count += 1

    print(f"\nExecution completed: {success_count} succeeded, {fail_count} failed")

    # Return non-zero exit code if any queries failed
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
