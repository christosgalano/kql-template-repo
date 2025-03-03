# Configuration Guide

This guide explains how to use the `.kql-config.yaml` configuration file to control the execution of KQL queries in the repository. The configuration follows the schema defined in `kql-config-schema.json`.

## Table of Contents

- [Schema Overview](#schema-overview)
- [Rules & Constraints](#rules--constraints)
- [Example Configurations](#example-configurations)
  - [Print Results to Console](#print-results-to-console)
  - [Include Specific Queries](#include-specific-queries)
  - [Exclude Specific Queries](#exclude-specific-queries)
  - [Custom Output Query: Length](#custom-output-query-length)
  - [Custom Output Query: Fields](#custom-output-query-fields)

## Schema Overview

The configuration file supports the following fields:

- **version** *(string, optional)*: Defines the schema version.
- **files** *(object, optional)*: Specifies which KQL files should be included or excluded from execution. Only one of `include` or `exclude` can be used.
  - `include` *(array of strings)*: List of KQL files to execute.
  - `exclude` *(array of strings)*: List of KQL files to ignore.
- **output** *(object, required)*: Configures how results are displayed and stored.
  - **formats** *(array, required)*: Defines one or more output formats.
    - `type` *(string, required)*: Defines the output type, either `console` (prints results) or `file` (stores results in structured files).
    - `query` *(string, optional)*: A JQ query filter to apply to results before output. Defaults to `.` (full result).
    - `path` *(string, required for `file`)*: Specifies the base folder for storing results. Relative to config file location. Results are stored under `{path}/{filename_template}`. Defaults to `repository-root/query-results`.
    - `filename_template` *(string, optional)*: Template for file naming. Supports `{query-folder}` and `{query}` placeholders. Relative to `path`. Defaults to `{query-folder}/{query}.json`.
    - `compression` *(string, optional)*: Defines compression type for file output. Options: `none`, `gzip`, `zip`. Defaults to `none`.

## Rules & Constraints

- If neither `include` nor `exclude` is specified, all KQL files in the folder are executed.
- If both `include` and `exclude` are provided, the configuration is invalid.
- `output.formats` must contain at least one output format.
- The `console` type always outputs to `stdout`.
- The `file` type requires a `path` field to specify the storage location.
- The `filename_template` must contain `{query-folder}` and `{query}` to ensure structured output storage.
- The `compression` field is optional and defaults to `none`.

> The configuration is validated against [`kql-config-schema.json`](/kql-config-schema.json).

## Example Configurations

### Print Results to Console

```yaml
version: "1.0"

output:
  formats:
    - type: console
```

This configuration allows all `.kql` files in the folder to be executed. Results are printed to `stdout`.

### Include Specific Queries

```yaml
version: '1.0'

files:
  include:
    - 'network-events.kql'
    - 'process-events.kql'

output:
  formats:
    - type: file
      path: "query-results"
```

This configuration will execute only `network-events.kql` and `process-events.kql`. Results are stored in `query-results/{query-folder}/{query}.json`.

### Exclude Specific Queries

```yaml
version: '1.0'

files:
  exclude:
    - 'deprecated-query.kql'

output:
  formats:
    - type: file
      path: "logs/security"
```

This configuration will execute all `.kql` files except `deprecated-query.kql`. Results are stored in `logs/security/{query-folder}/{query}.json`.

### Custom Output Query: Length

```yaml
version: '1.0'

files:
  include:
    - 'network-events.kql'

output:
  formats:
    - type: console
      query: 'length'
```

This configuration executes `network-events.kql` and displays the count of results.

### Custom Output Query: Fields

```yaml
version: '1.0'

files:
  include:
    - 'process-events.kql'

output:
  formats:
    - type: console
      query: 'map({Time: .TimeGenerated, Source: .Source})'

    - type: file
      query: '.'
      path: "logs"
      filename_template: "{query-folder}/all/{query}.json"
      compression: gzip

    - type: file
      query: 'map({Time: .TimeGenerated, Source: .Source})'
      path: "logs"
      filename_template: "{query-folder}/time-source/{query}.json"
      compression: gzip
```

This configuration executes `process-events.kql`:

- The first output format displays only the `TimeGenerated` and `Source` fields
- The second format stores the full result in `logs/process-events/all/process-events.kql.json`
- The third format stores the `TimeGenerated` and `Source` fields in `logs/process-events/time-source/process-events.kql.json`
