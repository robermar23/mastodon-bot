# mastodon-bot-cli

commands to automate interaction with your mastodon instance

## usage

### commands

#### init

simple test command to make sure app is installed and runs correctly

#### post

post content to your mastodon instance as a user/bot.

Current only supports posting from Dropbox folders and Plex Libraries

params:

```shell
mastodon_host=uri to your mastodon instance, i.e. robermar.social

#follow instruction here to create the mastodon params:
# https://docs.joinmastodon.org/client/token/
mastodon_client_id=
mastodon_client_secret=
mastodon_access_token= 

#follow external setup/dropbox for dropbox params
dropbox_client_id=
dropbox_client_secret=
dropbox_refresh_token=
dropbox_folder=

#follow external setup/openai for openai params
openai_api_key=

#define a prompt for a phrase about the post from openai completions endpoint
openai_default_completion=

#follow external setup/plex for plex params
plex_host=
plex_token=
```

if dropbox params are passed as source, a random file will be selected and posted

if openai params are passed, the status associated with the file will be a response from openai completion based off of your openai_default_completion text/question

if plex params are passed as a source, your instance will be queried for recenty added items and a summary of the media item will be posted along with a poster image of that content.

#### listen

listen for events in your mastodon instance for a given account (must be a bot!) and respond based off of params passed.

example:

```shell
mastodonbotcli listen $mastodon_host $mastodon_client_id $mastodon_client_secret $mastodon_access_token $openai_api_key $response_type
```

params:

```shell
mastodon_host=uri to your mastodon instance, i.e. robermar.social
#follow instruction here to create the mastodon params:
# https://docs.joinmastodon.org/client/token/
mastodon_client_id=
mastodon_client_secret=
mastodon_access_token= 

#follow external setup/openai for openai params
openai_api_key=
openai_chat_model=
openai_chat_temperature=
openai_chat_max_tokens=
openai_chat_top_p=
openai_chat_frequency_penalty=
openai_chat_presence_penalty=
openai_chat_max_age_hours=
openai_chat_persona=

#how you want the bot to respond to mentions.  
 #OPENAI_PROMPT: Ask a question/prompt to your bot and openai completions endpoint will respond
 #OPEN_AI_CHAT: Chat, have conversations with openai chat completions endpoint.
 #OPEN_AI_IMAGE: Prompt for an image description for DALL-E image endpoints

response_type=
```

### options

#### debugging

```shell
--debugging: 
```

add debug output for each command for troubleshooting purposes

## install

### Local Development

```shell
python -m pip install -r requirements/requirements_dev.txt
```

### Local Setup

Poetry is used as the package manager: `https://github.com/python-poetry/poetry`

If you do not have poetry installed:

```shell
POETRY_VERSION="1.4.0"
RUN pip install "poetry==$POETRY_VERSION"
```

Then install with poetry, including all dependencies.  

A virtual environment is automatically dreated

```shell
poetry install
```

use mastodonbotcli as an executable:

```shell
mastodonbotcli -help
```

### Container Image build and sample run

Build image locally:

```shell
docker build -t <your-tag> .
```

Sample container run command to execute mastodonbotcli locally:

```shell
docker run -it --entrypoint=mastodonbotcli <your-tag> init
 ```

### External Setup

#### Dropbox

- Create a new app in your DropBox account
  - you will need to refer to your app's APP_KEY and APP_SECRET that dropbox will provide

- Get a new access code for your app:

```shell
https://www.dropbox.com/oauth2/authorize?client_id=<APP_KEY>&token_access_type=offline&response_type=code
```

- pass access code to following curl command to get refresh token to save with config:

```shell
curl --location --request POST 'https://api.dropboxapi.com/oauth2/token' \
-u '<APP_KEY>:<APP_SECRET>'
-H 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'code=<ACCESS_CODE>' \
--data-urlencode 'grant_type=authorization_code'
```

- update config with app_key as client_id, app_secret as client_secret, new refresh token as refresh_token

#### open ai

- Sign up for an account at `https://openai.com/api/`

- Go to your Account settings, API Keys and create a new secret key
  - You will need to refer to this as openai_api_key for commands to use open ai

#### plex

- Assumption is that you have an existing Plex Server whose content you want to share info on.

- Follow instructions here to get your plex host and token: `https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/`

- Your plex_host will usually be something like:

```text
http|https://<private-ip>:32400
```

### Forward looking integrations

- Additional Plex data as a source for posts
  - post on metrics for plex
  - refresh libraries through commands sent to bot through mastodon (like remote control)

- Contentful as a destination for images/content generated by open ai requests

- News sources for a scheduled round up of news as a source for posts


