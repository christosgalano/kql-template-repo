# Azure
In order to execute KQL queries to your log analytics workspace, you have to register a new app and assign relevant permissions.

## Step 1, Azure App Registration

1. Sign in Azure, and head to the [Application Registration Portal](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps).
2. Choose New registration.
3. Then, choose a name and click Register.
> [!TIP]
> Choose a comfortable, yet recognisable name for your application.
4. From the overview page of the app you created, note the Application ID (client) and Directory ID (tenant).
5. Under Manage, choose Clients & secrets.
6. Choose New client secret. Add something relevant to the description (for example, Github Actions) and then the expiry time of your choice. Click add, copy both Value and Secret ID as you will need them later on.

## Step 2, Assign Log Analytics Workspace permissions

1. Navigate to the Log Analytics Workspace you want to connect to your Github Actions.
2. Choose Access control (IAM).
3. Choose Add and then, Add role assignment.
4. In the Role tab, select the Log Analytics Reader role and click Next.
5. On the Members tab, select Assign access to  User, group, or service principal.
6. Right to Members, clik Select members. Search for the application name you created in Step 1 and click Select.
7. Then click  Review + assign.

<p align="center">
  <img src="https://github.com/christosgalano/kql-template-repo/blob/main/docs/images/kql-azure-guide-01.jpg">
</p>

## Step 3, Assign federated credentials for Github
> [!IMPORTANT]
> Make sure you have a Github Repository ready to be assigned to this step.
1. Under Manage, Clients & secrets choose the Federated credentials Tab.
2. Choose Add credentials and from the Select scenario drop down menu, choose GitHub Actions deploying Azure resources.

<p align="center">
  <img src="https://github.com/christosgalano/kql-template-repo/blob/main/docs/images/kql-azure-guide-02.jpg">
</p>
