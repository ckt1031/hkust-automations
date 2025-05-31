# Outlook Summarizer

Summarize your Outlook emails with AI to Discord with separated types, like information, event, etc.

Very useful for school students who have a lot of emails to read.

## Setting Up Microsoft Email Summarization

We have to use the Microsoft Graph API to access the emails. To do this, we need to set up an application in Azure AD.

1. Go to the [Azure Portal](https://portal.azure.com/), and go to "App registrations" under "EntraID".
2. Click "New registration".
3. Fill in the details.
    - Multiple accounts supported: `Accounts in any organizational directory (Any ... Multitenant) and personal Microsoft accounts ...`
    - Redirect URI: `https://login.microsoftonline.com/common/oauth2/nativeclient` (Mobile)
4. After creating the application, go to "Certificates & secrets" and create a new client secret.
5. Copy the client secret and the application (client) ID.
6. Go to "API permissions" and add the following permissions:
    - `Mail.Read`
    - `Mail.Read.Shared`
    - `User.Read`
