# Azure Guide

In order to execute KQL queries to your log analytics workspace, you have to register a new app and assign relevant permissions.

## Step 1: Azure App Registration

1. Sign in Azure, and head to the [Application Registration Portal](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps).
2. Choose **New registration**.
3. Then, choose a name and click **Register**.

> [!TIP]
> Choose a comfortable, yet recognizable name for your application.

4. From the overview page of the app you created, note the Application ID (client) and Directory ID (tenant).

## Step 2: Assign Log Analytics Workspace permissions

1. Navigate to the **Log Analytics Workspace** you want to connect to your Github Actions.
2. Choose **Access control (IAM)**.
3. Choose **Add** and then, **Add role assignment**.
4. In the **Role** tab, select the Log Analytics Reader role and click Next.
5. On the **Members** tab, select **Assign access to User, group, or service principal**.
6. Right to **Members**, click **Select members**. Search for the application name you created in `Step 1` and click **Select**.
7. Then click **Review + assign**.

![Role Assignment](/assets/images/azure/role-assignment.jpg)

## Step 3: Assign federated credentials for Github

> [!IMPORTANT]
> Make sure you have created the GitHub repository following this [guide](/docs/github.md).

1. Under Manage, Clients & secrets choose the **Federated credentials** Tab.
2. Choose **Add credentials** and from the Select scenario drop down menu, choose **GitHub Actions deploying Azure resources**.

![Federated Credentials](/assets/images/azure/federated-credentials.jpg)

3. Add all the required information:

- Organization (your GitHub organization name)
- Repository (the name of your GitHub repository that will be assigned to materialize Actions)
- Entity type (choose Branch)
- Based on selection (type main)

4. Under **Credential details** choose a Name that would easily help identify these Federated credentials and add a description for your documentation.
5. Make sure all information is correct and click **Add**.
