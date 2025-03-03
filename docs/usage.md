# Usage Guide

## Table of Contents

- [Execution with GitHub Actions](#execution-with-github-actions)
- [Execution with Python Script](#execution-with-python-script)

> [!TIP]
> Make sure you have read the dedicated guidelines:
>
> - [Azure Guide](/docs/azure.md)
> - [GitHub Guide](/docs/github.md)
> - [Configuration Guide](/docs/configuration.md)

---

## Execution with GitHub Actions

When using **GitHub Actions**, it is recommended to keep the output file paths relative to the repository root and within `query-results/` if you want them to be uploaded as an artifact in the action workflow.

> [!IMPORTANT]
> Do not modify `path`  of each output format in the `.kql-config.yaml` file.
> You can modify the `filename_template` to store the results in a structured way.

### Recommended `.kql-config.yaml` for GitHub Actions

```yaml
version: '1.0'

files:
  include:
    - 'process-events.kql'

output:
  formats:
    - type: console
      query: '.' # show all results in the console

    - type: file
      query: '.' # store all results under `all/` folder
      filename_template: '{query-folder}/all/{query}.json'

    - type: file
      query: 'map({Time: .TimeGenerated, Source: .Source})' # example JQ transformation
      filename_template: '{query-folder}/time-source/{query}.json'

    # More output formats can be added here
    ...
```

📌 **Why this setup?**

- Keeps multiple queries structured.
- Ensures results are stored under `query-results/`, making them accessible for GitHub Actions' artifact upload.
- Allows different JSON transformations for each query.

If you do not need to have multiple output formats or customize with jq transformations, you can use the default `.kql-config.yaml` file.

```yaml
version: '1.0'

output:
  formats:
    - type: console
      query: '.'
    - type: file
      query: '.'
      path: query-results
      filename_template: '{query-folder}/{query}.json'
      compression: none
```

This is loaded automatically and will result in the following:

- All results are printed to the console.
- All results are stored under `query-results/${{ github.event.inputs.folder }}` with the query name as the filename.

---

## Execution with Python Script

If you are running queries locally via the Python script, follow these steps.

### 1. Set Up a Virtual Environment

It is recommended to use a Python virtual environment (`venv`) to manage dependencies.

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r .github/scripts/requirements.txt
```

### 2. Run the Query Execution Script

```sh
# Login to Azure
az login

# Run the script
python .github/scripts/execute_queries.py -w <workspace-id> -f library/<query-folder> -s kql-config-schema.json
```

📌 **Flags Explained:**

- `-w <workspace-id>`: Specifies the Azure Log Analytics workspace ID.
- `-f library/<query-folder>`: Specifies the folder containing the queries.
- `-s kql-config-schema.json`: Uses the schema file for validation.

Each `query-folder` can contain a dedicated `.kql-config.yaml` file to configure the output format. For more information, see the [Configuration Guide](/docs/configuration.md).

### 3. View Results

If `file` output is configured, results will be stored under `query-results/{query-folder}/{query}.json`.

To check the results:

```sh
ls -R query-results/
cat query-results/device/all/process-events.json
```

This setup ensures that results are structured and ready for further processing.
