# Azure
In order to execute KQL queries to your log analytics workspace, you have to register a new app and assign relevant permissions.

## Azure App Registration

1. Sign in Azure, and head to the [Application Registration Portal](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps).
2. Choose New registration.
3. Then, choose a name and click Register.
> [!TIP]
> Choose a comfortable, yet recognisable name for your application.
4. From the overview page of the app you created, note the Application ID (client) and Directory ID (tenant).
5. Under Manage, choose Clients & secrets.
6. Choose New client secret. Add something relevant to the description (for example, Github Actions) and then the expiry time of your choice. Click add, copy both Value and Secret ID as you will need them later on.
