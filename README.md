# KQL Template Repository

A comprehensive template for managing, executing, and organizing Kusto Query Language (KQL) queries against Azure Log Analytics workspaces. This repository provides a structured approach to query management with flexible output formats, automated execution, and comprehensive documentation.

## Table of Contents

- [Features](#features)
- [Documentation](#documentation)
- [Getting Started](#getting-started)
  - [1. Use This Template](#1-use-this-template)
  - [2. Azure Setup](#2-azure-setup)
  - [3. GitHub Configuration](#3-github-configuration)
  - [4. Execute Queries](#4-execute-queries)
- [Contributing](#contributing)
- [License](#license)

> [!TIP]
> Detailed documentation can be found in the corresponding [wiki page](https://github.com/christosgalano/kql-template-repo/wiki).

## Features

- **Structured Query Management**: Organize qu`eries in logical folders
- **Flexible Output Formats**: JSON, Table, TSV, YAML, and more
- **Multiple Output Destinations**: Console display or file output
- **Advanced Transformations**: Filter results using JMESPath queries
- **Compression Options**: Optimize storage with GZIP or ZIP compression
- **Automation**: GitHub Actions workflow for scheduled query execution
- **Local Execution**: Run queries from your development environment

## Documentation

For detailed information on using this repository, refer to:

- [Azure Guide](https://github.com/christosgalano/kql-template-repo/wiki/Azure): Azure setup
- [GitHub Guide](https://github.com/christosgalano/kql-template-repo/wiki/GitHub): GitHub Actions setup
- [Configuration Guide](https://github.com/christosgalano/kql-template-repo/wiki/Configuration): KQL config file format and options
- [Usage Guide](https://github.com/christosgalano/kql-template-repo/wiki/Usage): General usage instructions

## Getting Started

### 1. Use This Template

Click the **Use this template** button to create your own repository based on this template.

### 2. Azure Setup

1. Register an app in Azure Active Directory
2. Assign `Log Analytics Reader` permissions to the app
3. Configure federated credentials for GitHub Actions

### 3. GitHub Configuration

1. Set required secrets: `AZURE_CLIENT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `WORKSPACE_ID`
2. Store your KQL queries in folders under the `library` directory
3. Configure query outputs using `.kql-config.yaml` files

### 4. Execute Queries

#### Via GitHub Actions

1. Go to the **Actions** tab and run the **execute-queries** workflow
2. Specify the folder containing your queries

#### Via Python Script

```sh
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r .github/scripts/kql_query_executor/requirements.txt

# Login to Azure
az login

# Make sure you are in the repository root
python .github/scripts/kql_query_executor/main.py \
  -w <workspace-id> \
  -f library/<query-folder> \
  -s kql-config-schema.json
```

## Contributing

Information about contributing to this project can be found [here](CONTRIBUTING.md).

## License

This project is licensed under the [MIT License](LICENSE).
