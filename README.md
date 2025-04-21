
# AI Email Assistant

AI Email Assistant is an intelligent, automated email management tool designed to streamline and enhance productivity by integrating advanced natural language understanding with communication and scheduling platforms. Powered by LLaMA 3 Instruct, the assistant reads and categorizes emails via SimpleGmail API, comprehends context, and stores structured insights in a database. It interacts seamlessly with Custom Google Search, Google Calendar, and Slack to automate email triage, summarize threads, send replies, schedule meetings, and surface actionable tasks—transforming inbox overload into efficient workflows.


## Run Locally

Clone the project

```bash
  git clone https://github.com/btw-ImAsh/ai_mail_assistant.git
```

Go to the project directory

```bash
  cd my-project
```

Install dependencies

```bash
  pip install -r /path/to/requirements.txt
```

Authenticate

```bash
1. Create a Project in Google Cloud Console
Go to https://console.cloud.google.com

Create a new project or select an existing one.

2. Enable Gmail API (and others like Calendar if needed)
Navigate to APIs & Services > Library.

Search for Gmail API, Calendar API, etc.

Click Enable for each.

3. Configure OAuth Consent Screen
Go to APIs & Services > OAuth consent screen.

Choose External (for users outside your org) or Internal.

Fill in app details (app name, support email, etc.).

Add scopes like:

https://www.googleapis.com/auth/gmail

https://www.googleapis.com/auth/calendar

Add test users (if in testing mode).

4. Create OAuth 2.0 Credentials
Go to APIs & Services > Credentials > Create Credentials > OAuth client ID.

Choose application type:

For local dev: Desktop App

Save the Client ID and Client Secret.
```
You are now good to go!
## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`SLACK_WEBHOOK_URL`

`GOOGLE_CUSTOM_SEARCH_API`

`GOOGLE_SEARCH_ENGINE_ID`

To Retrieve Google Search API and Engine ID
```BASH
1. Get a Google API Key
Go to the Google Cloud Console.

Create a new project or select an existing one.

Navigate to APIs & Services > Credentials.

Click “Create Credentials” > “API key”.

Copy and save the generated API key.

(Optional but recommended) Click "Restrict key" to limit usage by IP, referrer, or API.

2. Enable the Custom Search API
In Cloud Console, go to APIs & Services > Library.

Search for Custom Search API.

Click Enable.

3. Create a Programmable Search Engine
Go to the Programmable Search Engine Dashboard.

Click “Get Started” or go to the Control Panel.

Under “Sites to Search”, enter any domain to begin (you can change this later to allow searching the entire web).

Click Create.

4. Get Your Search Engine ID
After creating the search engine, go to the Control Panel.

Click on your search engine.

Your Search Engine ID (aka cx) is listed under "Search engine ID".

5. (Optional) Set to Search the Whole Web
Go to the Control Panel for your engine.

Under Sites to Search, click Advanced.

Check “Search the entire web”.

Now you just need to set your .env file with these environment variables.
```
To get SLACK Webhook URL

```Bash
1. Go to Slack API: Create an App
Visit: https://api.slack.com/apps

Click “Create New App”

Choose “From scratch”

Name your app (e.g., AI Email Assistant)

Pick the workspace where you want to install it

Click “Create App”

2. Enable Incoming Webhooks
In the app settings, go to “Incoming Webhooks” (left sidebar)

Click the toggle to Activate Incoming Webhooks

3. Add a Webhook to a Slack Channel
Scroll down and click “Add New Webhook to Workspace”

Choose the channel you want the webhook to post to (public or private)

Click “Allow”

4. Copy the Webhook URL
After granting permission, you’ll be redirected to the settings

You’ll see your Webhook URL (looks like https://hooks.slack.com/services/XXXX/YYYY/ZZZZ)

Copy and save it securely in the .env file.
```
## Integration Diagram

![Untitled Diagram drawio](https://github.com/user-attachments/assets/e06b4a1f-5804-4dad-8c65-97d410ecc5f1)


If there is functionality you'd like to see added, or any bugs in this project, please let me know by posting an issue or submitting a pull request!
