# KQL Template Repository

```
                                                                                            ,--,    
                    ,--.                                           ,--.                  ,---.'|    
                ,--/  /|                 ,--,                  ,--/  /|     ,----..      |   | :    
             ,---,': / '               ,--.'|               ,---,': / '    /   /   \     :   : |    
             :   : '/ /                |  | :               :   : '/ /    /   .     :    |   ' :    
  .--.--.    |   '   ,                 :  : '               |   '   ,    .   /   ;.  \   ;   ; '    
 /  /    '   '   |  /       ,--.--.    |  ' |       ,---.   '   |  /    .   ;   /  ` ;   '   | |__  
|  :  /`./   |   ;  ;      /       \   '  | |      /     \  |   ;  ;    ;   |  ; \ ; |   |   | :.'| 
|  :  ;_     :   '   \    .--.  .-. |  |  | :     /    /  | :   '   \   |   :  | ; | '   '   :    ; 
 \  \    `.  |   |    '    \__\/: . .  '  : |__  .    ' / | |   |    '  .   |  ' ' ' :   |   |  ./  
  `----.   \ '   : |.  \   ," .--.; |  |  | '.'| '   ;   /| '   : |.  \ '   ;  \; /  |   ;   : ;    
 /  /`--'  / |   | '_\.'  /  /  ,.  |  ;  :    ; '   |  / | |   | '_\.'  \   \  ',  . \  |   ,/     
'--'.     /  '   : |     ;  :   .'   \ |  ,   /  |   :    | '   : |       ;   :      ; | '---'      
  `--'---'   ;   |,'     |  ,     .-./  ---`-'    \   \  /  ;   |,'        \   \ .'`--"             
             '---'        `--`---'                 `----'   '---'           `---`  
```
### 🚀 **Automate and run KQL queries at scale, using GitHub Actions.**

## Table of Contents

- [Introduction](#introduction)
  - [What is sKaleQL?](#what-is-skaleql?)
  - [Why should you use sKaleQL?](#why-should-you-use-skaleql?)
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

## Introduction

### What is sKaleQL?

**sKaleQL** is a comprehensive template for managing, executing, and organizing Kusto Query Language (KQL) queries against Azure Log Analytics Workspaces. This repository provides a structured approach to query management with flexible output formats, automated execution, and comprehensive documentation.

### Why should you use sKaleQL?

There is really no limit to how you can use this tool, it all depends on why you’re using Log Analytics Workspaces in the first place. Whether it’s for security, monitoring, auditing, or something else entirely, if you have a set of KQL queries you want to automate, **sKaleQL** is here to help. By combining the power of KQL with GitHub Actions, you can bring automation and efficiency into your workflows effortlessly.

Here are just a few examples of how sKaleQL can make a difference:

- Automated Health Checks: Regularly query for service errors, performance issues, or failed logins.
- Security and Threat Monitoring: Run scheduled KQL queries to detect anomalies, threats, or suspicious activity.
- Compliance Validation: Ensure logs reflect adherence to security and compliance standards.
- Reporting and Data Export: Generate and store logs or metrics as artifacts for analysis.
- Cost and Usage Monitoring: Track ingestion rates and resource usage for optimization.
- Incident Response Automation: Pre-build incident queries to speed up investigations.
- Incident Retrospectives: Pull relevant logs automatically after an incident for analysis and RCA (Root Cause Analysis).
- Business Metrics Tracking: Monitor and extract business-level KPIs (e.g., signups, payments, errors) if logged to Azure Monitor.
- Resource Inventory Tracking: Automatically query and export lists of resources (VMs, Containers, Storage) for auditing purposes.

## Features

- **Structured Query Management**: Organize queries in logical folders
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
