# GitHub Guide

## 1. Using This Template

To create a new repository using this template:

1. Navigate to the [kql-template-repo](https://github.com/christosgalano/kql-template-repo) repository.
2. Click **Use this template**.
3. Select **Create a new repository**.

![Using Template](/assets/images/github/use-template.png)

---

## 2. Setting Secret Values

To configure the necessary secrets for the repository, set the following values:

- **AZURE_CLIENT_ID**: Client ID of the Service Principal.
- **AZURE_SUBSCRIPTION_ID**: Subscription ID containing the Log Analytics Workspace.
- **AZURE_TENANT_ID**: Tenant ID of the Service Principal.
- **WORKSPACE_ID**: ID of the Log Analytics Workspace.

### Steps to set secrets

1. Navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Enter the name and value of the secret.
4. Click **Add secret**.

![Set Secrets](/assets/images/github/set-secrets.png)

---

## 3. Executing KQL Queries

1. Go to the **Actions** tab and select the **execute-queries** workflow.
2. Click **Run workflow**.
3. Enter the folder containing the KQL queries relative to `library` (e.g., `device`).
4. Click **Run workflow**.

![Run Workflow](/assets/images/github/run-workflow.png)

---

## 4. Viewing Query Results

---

## 5. Downloading Artifacts
