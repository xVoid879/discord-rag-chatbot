# Discord RAG Chatbot

Boldly going where hundreds have gone before.

## Installation and Setup
1. Visit [Discord's Developer portal](https://discord.com/developers/applications) and create a bot. Copy and save its bot token.
2. Visit [Groq](https://console.groq.com/keys) and create an API key.
3. Install [Python](https://www.python.org/downloads) alongside its pip package manager.
4. Clone or download+extract this repository.
5. Open a terminal of your choice and install the required libraries:
```bash
pip install -r "[your/path/to/]requirements.txt" -U
```
5. Open [Settings.py](Settings.py) in your editor of choice, and adjust the bot's settings as desired.
6. Launch the bot:
```bash
py "[your/path/to/]Launch.py" "[Discord bot token]" "[Groq API key]" "[privileged user #1's Discord ID]" ... "[privileged user #n's Discord ID]"
```

### Commands
- `->ask [query]`: Looks up and generates an answer for the provided query.
- `->addtext "[text #1]" ... "[text #n]"`: *(Privileged command)* Adds the provided texts to the vectorstore. To avoid mistakes with forgetting quotation marks, at least one text must be 2+ words. Quotation marks embedded in texts must be "escaped" by adding a backslash directly in front of them.
- `->load [filepath (optional)]`: *(Privileged command)* Loads the vectorstore from the provided filepath, or the last-used filepath if none is provided.
- `->save [filepath (optional)]`: *(Privileged command)* Saves the vectorstore to the provided filepath, or the last-used filepath if none is provided.

## Acknowledgments
A large proportion of this code was adapted from a similar project I had worked on alongside six other people. All rights to the corresponding pieces of code belong to their original authors.