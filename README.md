# Discord RAG Knowledge Base

Boldly going where hundreds have gone before.

This bot contains
- a vectorstore that texts can be saved, loaded, cleared, and have texts added to it.
- support for either printing the vectorstore's raw messages, or passing them to an AI to stitch the messages into a (hopefully-)coherent answer.
- optional caching for exact and similar queries, that can also be saved/loaded/cleared if desired.
- an optional global cooldown.
- the ability for elevated users to request existing messages be added to the vectorstore, pending the original author's approval.
- the ability to block/unblock specific users from interacting with the bot.
- the ability to trust/distrust specific users with elevated commands.
- the ability for users to <u>voluntarily</u> waive/reinvoke the need to ask for their approval prior to adding their messages to the vectorstore.
- the ability to save/load/clear pending vectorstore addition requests and pending waivers.
<!-- - the theoretical ability to return messages in other languages, should anyone be [willing to add translations](src/translations.py). -->

## Installation and Setup
1. Visit [Discord's Developer portal](https://discord.com/developers/applications) and create a bot. When invited to servers, it must have `Send message`, `Read message history`, and `Manage reactions` permissions. Copy and save its bot token.
2. *Optional: Visit [Groq](https://console.groq.com/keys) and create an API key.*
3. Install [Python 3.10 or above](https://www.python.org/downloads) alongside its pip package manager.
4. Clone or download+extract this repository.
5. Open a terminal of your choice and install the required libraries:
```bash
pip install -r "[your/path/to/]requirements.txt" -U
```
6. Open [Settings.py](Settings.py) in your editor of choice, and adjust the bot's settings as desired. You can also alter some of the bot's printed messages in [Translations.py](Translations.py) if desired.
7. Launch the bot. If no Groq API key is provided, the bot will solely print the most relevant messages from the vectorstore when queried.
```bash
py "[your/path/to/]Main.py" "[Discord bot token]" "[Groq API key (optional)]"
```

## Commands
This bot is primarily interacted with via slash commands or pinging it.
- `[/ask or ping the bot] [query]`: Looks up and generates an answer for the provided query.
- `/help [command (optional)]`: Prints the bot's purpose and list of commands, or a single command if one is specified.
- `/ping`: Returns the bot's latency.
- `[ping the bot] permit`: Adds oneself to the permitting group, allowing trusted users to add any of their messages to the vectorstore without having to individually request permission.
- `/revoke`: Removes oneself from the permitting group, revoking the permission to trusted users granted by `permit`.
- `/getsize [Blocked Group|Cache|Permitting Group|Permitting Requests|Trusted Group|Vectorstore|Vectorstore Requests]`: Returns the number of entries in the provided group/cache/requests list/vectorstore.
- `/contains [Blocked Group|Permitting Group|Trusted Group] [user ID (optional)]`: Returns whether the provided group contains the command executor, or the provided user if one is specified.
### Trusted commands
- `/add [Blocked Group|Trusted Group|Vectorstore] [user ID/message URL]`: Directly adds the provided user ID, to the provided group, or *requests to* add the linked message to the provided vectorstore.
- `clear [All|Blocked Group|Cache|Permitting Group|Permitting Requests|Trusted Group|Vectorstore Requests]`: Clears the provided group/cache/requests list/vectorstore, respectively.
- `/remove [Blocked Group|Trusted Group] [user ID]`: Removes the provided user from the provided group.
### Owner commands
- `save [All|Blocked Group|Cache|Permitting Group|Permitting Requests|Trusted Group|Vectorstore|Vectorstore Requests] [filepath (optional)]`: Saves the provided group/cache/requests list/vectorstore to their last-used filepath, or the provided filepath if specified.
- `load [All|Blocked Group|Cache|Permitting Group|Permitting Requests|Trusted Group|Vectorstore|Vectorstore Requests] [filepath (optional)]`: Loads the provided group/cache/requests list/vectorstore from their last-used filepath, or the provided filepath if specified.

### Reactions
For messages sent after the bot is added, trusted users can request to add an existing message to the vectorstore by adding the `DISCORD_REQUEST_ADDITION_EMOJI` reaction specified in [Settings.py](Settings.py). This requires the original author's approval unless the requester *is* the original author, or the author has voluntarily added himself/herself to the permitting group.

A current limitation is that the bot cannot detect reactions on messages sent prior to the bot last coming online. For those messages, use `/add Vectorstore [URL]` instead.

## Acknowledgments
For the original code of this bot, much of it was adapted from a similar project I had worked on alongside six other people. All rights to unmodified corresponding pieces of code belong to their original authors. However, the code has also been substantially expanded since then.

Thank you to Fanda857, [Meox](https://github.com/69b69t), [Opal](https://github.com/Opalinium), and [Tomlacko](https://github.com/Tomlacko) for providing insights and feedback. Thank you also to [Kris](https://github.com/Kludwisz), Pokeruto898, and [xVoid879](https://github.com/xVoid879) for discovering bugs in the program.

Pull requests or issue filings are welcome.