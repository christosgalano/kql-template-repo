# Configuration Guide

This guide explains how to use the `.kql-config.yaml` configuration file to control the execution of KQL queries in the repository. The configuration follows the schema defined in `kql-config-schema.json`.

## Table of Contents

- [Schema Overview](#schema-overview)
- [Rules & Constraints](#rules--constraints)
- [Default Behavior](#default-behavior)
- [Example Configurations](#example-configurations)
  - [Basic Configuration](#basic-configuration)
  - [Multiple Queries with Custom Outputs](#multiple-queries-with-custom-outputs)
  - [Custom JMESPath Query](#custom-jmespath-query)
  - [Multiple Output Formats](#multiple-output-formats)

## Schema Overview

> [!NOTE]
> The configuration is validated against [`kql-config-schema.json`](/kql-config-schema.json).

The configuration file supports the following fields:

- **version** *(string, optional)*: Defines the schema version.
- **queries** *(array, optional)*: Individual query configurations with specific execution settings (see [Query Configuration](#query-configuration) for details).

> ![!IMPORTANT]
> If `queries` is specified in the configuration file, only the queries listed will be executed.

### Query Configuration

Each query configuration object contains the following fields:

- `file` *(string, required)*: Path to the `.kql` file containing the query. Relative to the configuration file.
- `output` *(array, optional)*: Output formats for this specific query, overriding defaults (see [Output Format](#output-format) for details).

### Output Format

Each output format object contains the following fields:

- `format` *(string, required)*: Output format. Supported values are `json,jsonc,none,table,table,tsv,yaml,yamlc`.
- `query` *(string, optional)*: JMESPath query string to apply. See [JMESPath](http://jmespath.org/) for more information and examples.
- `file` *(string, optional)*: File to write the output to. Relative to the configuration file. If not specified, the output is written to the console. Defaults to a sanitized version of the query file path where:
  - Directory separators are replaced with underscores
  - The `.kql` extension is removed
  - Format extension is added (`json`, `yaml`, `tsv`, and `txt`)
  - For example, a query file at `path/to/query.kql` will result in a default filename of `path_to_query.json`
- `compression` *(string, optional)*: Compression type for the output file. Supported values are `gzip`, and `zip`. If not specified, no compression is applied.

## Rules & Constraints

- By default, all KQL files in the folder are executed with JSON output to the console.
- For queries listed in the configuration, the specified output settings are used.
- For `file` directories are created if they do not exist.
- All query files must end with `.kql` extension.
- `query` can be multiline using `>-`.
- If format is `none` the `file` field is ignored.
- The extension mapping for formats is the following:
  - `json` and `jsonc` are saved as `.json`
  - `yaml` and `yamlc` are saved as `.yaml`
  - `tsv` is saved as `.tsv`
  - `table` is saved as `.txt`

> [!IMPORTANT]
> `file` must not contain any whitespace characters or it will result in an error.

## Default Behavior

When no configuration file is provided or when specific elements are omitted:

- **No Configuration File**: All KQL files in the specified folder and its subdirectories will be executed with JSON output to the console.
- **No Queries Section**: All KQL files in the specified folder and its subdirectories will be executed with JSON output to the console.
- **No Output Section** for a query: The query results will be output to the console in JSON format.
- **JMESPath query Not Specified**: No JMESPath query is applied to the output.
- **Compression Not Specified**: No compression is applied to output files.

## Example Configurations

### Basic Configuration

```yaml
version: "1.0"

queries:
  - file: 'example.kql'
    output:
      - format: jsonc
      - format: json
        file: 'query-results/output.json'
        compression: gzip
```

This configuration executes the specified query. Results are printed to the console in JSONC format and saved to `query-results/output.json` in JSON format with GZip compression.

### Multiple Queries with Custom Outputs

```yaml
version: '1.0'

queries:
  - file: 'device.kql'
    output:
      - format: none

  - file: 'user.kql'
    output:
      - format: yaml
        # file: 'user.yaml' - default

  - file: 'network/nsg.kql'
    output:
      - format: tsv
        # file: 'network_nsg.tsv' - default

  - file: 'network/vm.kql'
    output:
      - format: table
        file: subdir/vm.txt
```

This configuration executes four queries:

- `device.kql` with no output
- `user.kql` with YAML output saved to `user.yaml`
- `network/nsg.kql` with TSV output saved to `network_nsg.tsv`
- `network/vm.kql` with table output saved to `subdir/vm.txt` (`subdir` directory is created if it does not exist)

### Custom JMESPath Query

```yaml
version: '1.0'

queries:
  - file: 'network-events.kql'
    output:
      - format: table
        query: >-
          reverse(sort_by([].{
            Time: TimeGenerated,
            Action: ActionType,
            Endpoint: join(':', [to_string(RemoteIP), to_string(RemotePort)])
          }, &Time))[:10]
```

This configuration executes `network-events.kql` and displays the top 10 results in a table format with custom columns.

### Multiple Output Formats

```yaml
version: '1.0'

queries:
  - file: 'security-events.kql'
    output:
      - format: jsonc

      - format: json
        file: 'logs/security-events.json'
        compression: gzip

      - format: json
        query: 'events[?severity=='critical']'
        file: 'alerts/critical.json'

      - format: json
        query: 'events[?severity=='high']'
        file: 'alerts/high.json'

      - format: json
        query: 'events[?severity=='high']'
        file: 'alerts/medium.json'

      - format: json
        query: 'events[?severity=='high']'
        file: 'alerts/low.json'
```

This configuration executes `security-events.kql` with the following outputs:

- Prints the results in JSONC format
- Saves the full results in `logs/security-events.json` with GZip compression
- Saves the results filtered by severity in separate files in the `alerts` directory
