# HKUST Information Push

A set of tools to push information to HKUST students.

We current support pushing information to Discord via webhooks, other platforms can be added in the future.

## Setting Up Microsoft Email Summarization

We have to use the Microsoft Graph API to access the emails. To do this, we need to set up an application in Azure AD.

1. Go to the [Azure Portal](https://portal.azure.com/), and go to "App registrations" under "Entra ID".
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

## Setting Up Canvas Instructor API

1. Go to <https://canvas.ust.hk/profile/settings>
2. Scroll down to "Approved Integrations" and click on "New Access Token"
3. Fill in the details and click "Generate Token"
4. Copy the token and save to `.env` file based on the [.env.example](.env.example) file
