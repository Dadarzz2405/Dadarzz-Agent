# 🔗 Google Integration Setup Guide

If you want the AI-Agent to read real emails, interact with real Google Drive files, and check real calendars, you need to connect it to Google Cloud. 

Since this is a Desktop app that you distribute to users, you will create a **Desktop App OAuth Client**. Here is the step-by-step guide.

---

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.
3. Click the Project Dropdown at the top left → **New Project**.
4. Name it `"Dadarzz-Agent"` and click **Create**.

### Step 2: Enable the Required APIs
1. In the search bar at the top, search for and enable the following APIs one by one:
   - **Gmail API**
   - **Google Drive API**
   - **Google Calendar API**
   *(Click on each one in the search results, then click the blue "Enable" button).*

### Step 3: Configure the OAuth Consent Screen
This is the screen users see when your app asks them to log in.
1. On the left sidebar, go to **APIs & Services** → **OAuth consent screen**.
2. Choose **External** (so anyone can use it, not just people in your organization) and click Create.
3. **App Information**:
   - App name: `Dadarzz AI-Agent`
   - User support email: `[your email]`
   - Developer contact info: `[your email]`
4. Click **Save and Continue**.
5. **Scopes**: You don't strictily need to add them here, but if you do, add: `.../auth/gmail.modify`, `.../auth/drive`, and `.../auth/calendar`. Click **Save and Continue**.
6. **Test Users**: Add your own email here first while testing. Later, you can publish the app so anyone can use it.
7. Click **Save and Continue** until you're done.

### Step 4: Generate `credentials.json`
Now you need the file that actually links your code to this project.
1. On the left sidebar, go to **Credentials**.
2. Click **+ CREATE CREDENTIALS** at the top → select **OAuth client ID**.
3. **Application Type**: Select **Desktop app** *(This is CRITICAL!)*.
4. Name: `Dadarzz Desktop`
5. Click **Create**.
6. A popup will appear. Click the **DOWNLOAD JSON** button.
7. Rename the downloaded file to exactly `credentials.json`.
8. Move `credentials.json` into your `Dadarzz-Agent` folder.

---

### Step 5: Distributing it via GitHub Actions

Because you are distributing this app via GitHub Actions, your CI automated builder needs the `credentials.json` file in order to package it into the `.zip` for your users.

Currently, `credentials.json` is ignored by Git. Here is how to include it so your users' apps will connect to Google:

1. Open your `.gitignore` file.
2. Remove or delete the line: `credentials.json`
3. Save the `.gitignore` file.
4. Commit it to GitHub:
   ```bash
   git add .gitignore credentials.json
   git commit -m "Add Google OAuth credentials for distribution"
   git tag v1.3.0
   git push && git push --tags
   ```

*(**Security Note:** According to Google's official documentation, the Client Secret inside a "Desktop App" OAuth JSON is not considered a secret because anyone can extract it from the `.exe` anyway. It is perfectly safe to commit this specific type of `credentials.json` to GitHub.)*

---

### Wait, how do I actually write the code to use it?

You already wrote the Google Tools logic in `tools/gmail_tool.py`, `tools/drive_tool.py`, etc.! However, right now `main.py` is hardcoded to give a `placeholder_token`. 

Once you have your `credentials.json` ready, you just need to implement the standard Python `google-auth-oauthlib.flow` inside `main.py`'s `/google_auth` route to properly request the user's login and save their real token instead of the placeholder. Let me know when you've done the cloud setup and want help writing the actual login flow!
