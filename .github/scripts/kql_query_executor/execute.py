import gzip
import logging
import os
import shutil
import subprocess
from pathlib import Path

from config import get_output_configs_for_query
from model import CompressionType, KQLConfig, OutputFormat


def execute_query(
    folder_path: str, query_file: str, workspace_id: str, config: KQLConfig
) -> bool:  # noqa: C901
    """Execute a KQL query and process the results."""
    # Convert folder_path to Path object
    base_path = Path(folder_path)
    query_path = base_path / query_file

    # Verify query file exists
    if not query_path.exists():
        logging.error(f"Query file not found: {query_path}")
        return False

    logging.info(f"Executing {query_path}...")

    # Get output configurations for this query
    output_configs = get_output_configs_for_query(config, query_file)
    if not output_configs:
        logging.error(f"No output configuration found for query: {query_path}")
        return False

    try:
        # Process each output format
        for fmt in output_configs:
            # Skip processing if format is NONE
            if fmt.format == OutputFormat.NONE:
                logging.info(f"Skipping output for {query_path} (format: none)")
                continue

            # Build Azure CLI command with output format
            cmd = [
                "az",
                "monitor",
                "log-analytics",
                "query",
                "-w",
                workspace_id,
                "--analytics-query",
                f"@{query_path}",
                "--output",
                fmt.format.value,  # Use format enum value directly
            ]

            # Add JMESPath query if specified
            if fmt.query:
                # Clean up the query string:
                # 1. Remove newlines and extra spaces
                # 2. Escape any existing quotes
                # 3. Wrap in quotes if needed
                clean_query = fmt.query.strip().replace("\n", " ").replace("  ", " ")
                cmd.extend(["--query", clean_query])

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
            filtered_result = result.stdout.strip()

            # Process the results
            if not fmt.file:
                # Display to console
                print(f"Results for {query_file}")
                print("-" * 80)
                print(filtered_result)
                print(end="\n\n")
                logging.info(f"Results for {query_file} displayed to console")
                continue

            # Process file output
            output_file = fmt.file

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Write the results to file
            with open(output_file, "w") as f:
                f.write(filtered_result)
            logging.info(f"Results saved to {output_file}")

            # Apply compression if specified
            if fmt.compression:
                if fmt.compression == CompressionType.GZIP:
                    with (
                        open(output_file, "rb") as f_in,
                        gzip.open(f"{output_file}.gz", "wb") as f_out,
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

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing query {query_path}: {e}")
        if hasattr(e, "stderr") and e.stderr:
            logging.error(f"Error details: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error processing {query_path}: {e}")
        return False
