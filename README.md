# Migrate your subscriptions and playlists to a new account

This process is free, but you will need to follow the instructions below.

You need to configure a new project in Google Cloud and enable the API for YouTube. You will then need to generate credentials for this API, and run the Python script available in this repository [main.py](https://github.com/Ze1598/youtube-migrate-subs-playlists/blob/main/main.py).


# Pre-requisites

## Python libraries

You need to install libraries for Google APIs. The command below installs all the relevant libraries. 

Other library references within the script are built-in on Python 3.10 and above.

```
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Google Cloud Project & YouTube Data API enablement

* Go to the Google Cloud Console to [create a new project](https://console.cloud.google.com/projectcreate)
* Enable the [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) (you can also search for the API via the search box at the top or navigate through the APIs & Services menu)
* Within the APIs & Services menu, go to the Credentials submenu and [create new OAuth Client ID credentials](https://console.cloud.google.com/apis/credentials/oauthclient)
* When prompted for Application Type, choose Desktop App. This is because the script uses the `InstalledAppFlow` class from `google_auth_oauthlib.flow`, which is designed for desktop applications
* Download the client secrets file and rename it to client_secrets.json - download the file into the same directory as the main.py script and no further changes are required

P.S.: this script will require the API / the credentials to have the following scopes, aka the permissions, youtube.readonly and youtube.force-ssl. Users will be informed and their consent is required during execution of the script.

## Adding users to your project
One issue I faced during testing is that I couldn't authenticate successfully. Even when using the account that owns this project on Google Cloud.

This happens for security purposes: when initially created, the project will be in Testing status, i.e. intended for development purposes only and a limited audience. But that is not a concern over personal use of this integration.

The solution is to manually add your source and destination accounts as users of this app. They will still get a warning that this is not a verified application during authentication. However, this is trusted code after all. For the effect, go to [Audience](https://console.cloud.google.com/auth/audience) under Google Auth Platform and add your user accounts as Test Users.


# Running the script

After completing the pre-requisites, go to the command line and run

```python main.py```

The script will:

* Prompt you to authenticate both your source and destination YouTube accounts in the browser (standard Google account authentication page)
* (After authentication, follow the instructions in the command line)
* Ask for the names of playlists you want to migrate and for those migrate the playlists with all their videos
* Ask if you want to migrate subscriptions and if yes migrate all subscriptions
* Provide progress updates during the migration

## Important notes

* The script requires appropriate OAuth scopes to read from the source account and write to the destination account
* It handles API quota limits and potential errors
* The migration is done sequentially to avoid rate limiting issues
* You'll need to authorize the application for both accounts when running it for the first time
