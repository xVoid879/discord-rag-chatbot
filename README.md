# Discord RAG Chatbot

Boldly going where hundreds have gone before.

This bot contains
- a vectorstore that texts can be saved, loaded, and have texts added to/deleted from it.
- support for either printing the vectorstore's raw messages, or passing them to an AI to stitch the messages into a (hopefully-)coherent answer.
- optional caching for exact and similar queries, that can also be saved/loaded if desired.
- an optional global cooldown.
- the ability for elevated users to request existing messages be added to the vectorstore, pending the original author's approval.
- the ability to block/unblock specific users from interacting with the bot.
- the ability to trust/distrust specific users with elevated commands.
- the ability for users to <u>voluntarily</u> waive/reclaim the need to ask for their approval prior to adding their messages to the vectorstore.
- the ability to save/load pending vectorstore addition requests and/or pending waivers.
<!-- - the theoretical ability to return messages in other languages, should anyone be [willing to add translations](src/translations.py). -->

## Installation and Setup
1. Visit [Discord's Developer portal](https://discord.com/developers/applications) and create a bot. When invited to servers, it must have `Send message`, `Read message history`, and `Manage reactions` permissions. Copy and save its bot token.
2. Optional: Visit [Groq](https://console.groq.com/keys) and create an API key.
3. Install [Python 3.10 or above](https://www.python.org/downloads) alongside its pip package manager.
4. Clone or download+extract this repository.
5. Open a terminal of your choice and install the required libraries:
```bash
pip install -r "[your/path/to/]requirements.txt" -U
```
6. Open [Settings.py](Settings.py) in your editor of choice, and adjust the bot's settings as desired.
7. Launch the bot. If no Groq API key is provided, the bot will solely print the most relevant messages from the vectorstore.
```bash
py "[your/path/to/]Main.py" "[Discord bot token]" "[Groq API key (optional)]"
```

## Commands
This bot is primarily interacted with via pinging it or slash commands.
- `[query]`: Looks up and generates an answer for the provided query.
- `/help`: Prints the bot's purpose and list of commands.
- `/ping`: Returns the bot's latency.
- `hasrole [blocked|permitting|trusted] [user ID (optional)]`: Returns whether a user (defaulting to yourself) is blocked/permitting/trusted, respectively.
- `permit`: Adds oneself to the permitting group, allowing trusted users to add any of their messages to the vectorstore without having to individually request permission.
- `revoke`: Removes oneself from the permitting group, revoking the permission to trusted users granted by `permit`. 
### Trusted commands
- `addtext "[text]"`: Directly adds the provided text to the vectorstore.<!-- To avoid mistakes with forgetting quotation marks, the text must be 2+ words. Quotation marks embedded in texts must be "escaped" by adding a backslash directly in front of them.-->
- `clear [all|blocked_group|cache|permitting_group|permitting_requests|trusted_group|vectorstore_requests]`: Clears the provided group/cache/requests list, respectively.
- `save [all|blocked|permitting|trusted|vectorstore] [filepath (optional)]`: Saves the provided group/cache/requests list/vectorstore to the provided filepath, or their last-used filepath if none is provided.
- `load [all|blocked|permitting|trusted|vectorstore] [filepath (optional)]`: Loads the provided group/cache/requests list/vectorstore from the provided filepath, or their last-used filepath if none is provided.
- `block [user ID #1] ... [user ID #n]`/`unblock [user ID #1] ... [user ID #n]`: Adds or removes user(s) to the blocked group, respectively.
- `trust [user ID #1] ... [user ID #n]`/`distrust [user ID #1] ... [user ID #n]`: Adds or removes user(s) to the trusted group, respectively.

### Reactions
For messages sent after the bot is added, trusted users can request to add an existing message to the vectorstore by adding the `DISCORD_REQUEST_ADDITION_EMOJI` reaction specified in [Settings.py](Settings.py). This requires the original author's approval unless the requester *is* the original author, or the author has voluntarily added himself/herself to the permitting group.

## Acknowledgments
A sizable proportion of the original code was adapted from a similar project I had worked on alongside six other people. All rights to the corresponding pieces of code belong to their original authors. (However, the code has also been expanded substantially since then.)

Pull requests or issue filings are welcome.