# End-to-End Example Guide

This guide provides a complete, practical example of how to set up and use the repository to execute KQL queries in batches using both **GitHub Actions** and **local execution with Python**.

## Table of Contents

- [Scenarios](#scenarios)
  - [Setting Up a New Query Folder](#setting-up-a-new-query-folder)
  - [Updating Queries](#updating-queries)
- [Running Queries](#running-queries)
  - [With GitHub Actions](#with-github-actions)
  - [With Python locally](#with-python-locally)

---

## Scenarios

### Setting Up a New Query Folder

#### 1. Create a New Folder

Navigate to the `library/` directory and create a new subdirectory, e.g., `library/security`.

```sh
mkdir library/security
```

#### 2. Add KQL Query Files

Place your `.kql` query files inside the newly created directory. Example:

```sh
touch library/security/user-access.kql
```

Edit `user-access.kql` to contain a sample KQL query:

```kql
SecurityEvent
| where EventID == 4625
| project TimeGenerated, Account, LogonType
```

#### 3. Add a `.kql-config.yaml` File

Create a `.kql-config.yaml` file inside `library/security/` to specify execution settings.

Recommended `.kql-config.yaml`:

```yaml
version: '1.0'
files:
  include:
    - 'user-access.kql'
output:
  formats:
    - type: console
      query: '.'
    - type: file
      query: '.'
      filename_template: '{query-folder}/all/{query}.json'
    - type: file
      query: 'map({Time: .TimeGenerated, Source: .Source})'
      filename_template: '{query-folder}/time-source/{query}.json'
```

#### 4. Commit and Push Changes

```sh
git add library/security/
git commit -m "Added security query folder"
git push origin main
```

### Updating Queries

#### 1. Adding a New Query

To add a new query to an existing folder, place another `.kql` file inside, e.g., `library/security/admin-logins.kql`:

```kql
SecurityEvent
| where EventID == 4672
| project TimeGenerated, Account, PrivilegeList
```

Update `.kql-config.yaml` if needed:

```yaml
version: '1.0'
files:
  include:
    - 'user-access.kql'
    - 'admin-logins.kql'
output:
  formats:
    - type: console
      query: '.'
    - type: file
      query: '.'
      filename_template: '{query-folder}/all/{query}.json'
```

#### 2. Removing a Query

```sh
rm library/security/user-access.kql
```

Update `.kql-config.yaml` accordingly and commit the changes:

```sh
git add library/security/
git commit -m "Removed user-access query"
git push origin main
```

---

## Running Queries

### With GitHub Actions

1. Navigate to **GitHub Actions**.
2. Select **execute-queries** workflow.
3. Click **Run workflow**.
4. Enter the subdirectory name (e.g., `security`).
5. Click **Run workflow**.

The workflow will:

- Validate folder existence.
- Authenticate with Azure.
- Install required dependencies.
- Execute queries.
- Upload results to **GitHub Actions artifacts** under `query-results/`.

### **GitHub Actions Workflow (`execute-queries.yaml` Extract)**

```yaml
- name: Upload results
  uses: actions/upload-artifact@v4
  with:
    name: query-results
    path: query-results
```

📌 **Ensure `path` in `.kql-config.yaml` is set relative to repo root to `query-results/` for artifact upload.**

### With Python locally

#### 1. Set Up a Virtual Environment

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r .github/scripts/requirements.txt
```

#### 2. Run the Query Execution Script

```sh
python .github/scripts/execute_queries.py -w <WORKSPACE_ID> -f library/security -s kql-config-schema.json
```

📌 **Flags Explained:**

- `-w <WORKSPACE_ID>`: Specifies the Azure Log Analytics workspace ID.
- `-f library/security`: Runs queries in `library/security/`.
- `-s kql-config-schema.json`: Uses the schema file for validation.

#### 3. View Results

```sh
ls -R query-results/
cat query-results/security/all/user-access.json
```

This setup ensures results are structured, validated, and ready for further processing.
