# Discord RAG Chatbot

Boldly going where hundreds have gone before.

## Installation and Setup
1. Visit [Discord's Developer portal](https://discord.com/developers/applications) and create a bot. When invited to servers, it must have `Send message`, `Read message history`, and `Manage reactions` permissions. Copy and save its bot token.
2. Optional: Visit [Groq](https://console.groq.com/keys) and create an API key.
3. Install [Python](https://www.python.org/downloads) alongside its pip package manager.
4. Clone or download+extract this repository.
5. Open a terminal of your choice and install the required libraries:
```bash
pip install -r "[your/path/to/]requirements.txt" -U
```
6. Open [Settings.py](Settings.py) in your editor of choice, and adjust the bot's settings as desired.
7. Launch the bot. If no Groq API key is provided, the bot will solely print the most relevant messages from the vectorstore.
```bash
py "[your/path/to/]Launch.py" "[Discord bot token]" "[Groq API key (optional)]"
```

### Commands
This bot is primarily interacted with via pinging it.
- `[query]`: Looks up and generates an answer for the provided query.
- `help`: Prints the bot's purpose and list of commands.
- `ping`: Returns the bot's latency.
- `hasrole [blocked|permitting|trusted] [user ID]`: Returns whether a user is blocked/permitting/trusted, respectively.
- `permit`: Adds oneself to the permitting group, allowing trusted users to add any of their messages to the vectorstore without having to individually request permission.
- `revoke`: Removes oneself from the permitting group, revoking the permission to trusted users granted by `permit`. 
#### Trusted commands
- `addtext "[text]"`: Directly adds the provided text to the vectorstore.<!-- To avoid mistakes with forgetting quotation marks, the text must be 2+ words. Quotation marks embedded in texts must be "escaped" by adding a backslash directly in front of them.-->
- `clear [blocked|cache|permitting|trusted]`: Clears the blocked list/cache/permitting list/trusted list, respectively.
- `save [blocked|permitting|trusted|vectorstore] [filepath (optional)]`: Saves the blocked list/permitting list/trusted list/vectorstore to the provided filepath, or their last-used filepath if none is provided.
- `load [blocked|permitting|trusted|vectorstore] [filepath (optional)]`: Loads the blocked list/permitting list/trusted list/vectorstore from the provided filepath, or their last-used filepath if none is provided.
- `block [user ID #1] ... [user ID #n]`/`unblock [user ID #1] ... [user ID #n]`: Adds or removes user(s) to the blocked group, respectively.
- `trust [user ID #1] ... [user ID #n]`/`distrust [user ID #1] ... [user ID #n]`: Adds or removes user(s) to the trusted group, respectively.

### Reactions
For messages sent after the bot is added, trusted users will ultimately be able to request to add existing messages to the vectorstore, pending the original author's permission. This however is still under development.

## Acknowledgments
A large proportion of this code was adapted from a similar project I had worked on alongside six other people. All rights to the corresponding pieces of code belong to their original authors.