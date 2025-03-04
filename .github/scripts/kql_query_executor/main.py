#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from config import find_config_file, get_applicable_files, load_config
from execute import execute_query
from model import KQLConfig
from utils import setup_logging


def main() -> None:
    """
    Execute KQL queries from a folder based on configuration.

    By default, all KQL files in the specified folder are executed with JSON output to stdout.
    If a configuration file is found, query-specific settings are applied.
    """
    parser = argparse.ArgumentParser(description="Execute KQL queries from a folder")
    parser.add_argument(
        "-f", "--folder", required=True, help="Path to the folder containing KQL files"
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

    # Validate folder exists
    folder_path = args.folder
    if not os.path.isdir(folder_path):
        logging.error(f"Folder {folder_path} does not exist")
        sys.exit(1)

    # Load configuration
    config_path = args.config or find_config_file(folder_path)
    if config_path:
        logging.info(f"Using config file: {config_path}")
        config = load_config(config_path, args.schema)
    else:
        logging.info("No config file found, using default JSON output for all queries")
        config = KQLConfig()  # Default config with JSON output to stdout

    # Find all KQL files in the folder
    applicable_files = get_applicable_files(folder_path, config)
    if not applicable_files:
        logging.info("No KQL files found in the specified folder")
        sys.exit(0)

    logging.info(f"Found {len(applicable_files)} KQL file(s) to execute")

    # Execute each query
    success_count, fail_count = 0, 0
    for file_name in applicable_files:
        if execute_query(folder_path, file_name, args.workspace_id, config):
            success_count += 1
        else:
            fail_count += 1

    # Report results
    logging.info(f"Execution completed: {success_count} succeeded, {fail_count} failed")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
