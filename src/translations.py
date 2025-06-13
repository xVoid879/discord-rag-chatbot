from typing import Iterable, Literal, TypeAlias

SupportedLanguages: TypeAlias = Literal["English"]

def getLanguagePlural(language: SupportedLanguages, count: int) -> str:
	"""Returns the (approximate) plural for the provided language and count."""
	match language:
		case "English": return "" if count == 1 else "s"
		# TODO: How can I translate this error?
		case _: raise RuntimeError("Unknown or unsupported language provided.")


# ai.py
class AITexts:
	# Supported substitutions: [context]
	CONTEXT_ADDITION: dict[SupportedLanguages, str] = {
		"English": "Context: [context]"
	}
	# Supported substitutions: [count]
	INVALID_MAX_INPUT_CHARACTERS_TYPE: dict[SupportedLanguages, str] = {
		"English": "Invalid maximum input characters count provided: [count]"
	}
	# Supported substitutions: [count]
	INVALID_MAX_OUTPUT_CHARACTERS_TYPE: dict[SupportedLanguages, str] = {
		"English": "Invalid maximum output characters count provided: [count]"
	}
	# Supported substitutions: [prompt]
	INVALID_SYSTEM_PROMPT: dict[SupportedLanguages, str] = {
		"English": "Invalid system prompt provided: [prompt]"
	}
	# Supported substitutions: [temperature]
	INVALID_TEMPERATURE: dict[SupportedLanguages, str] = {
		"English": "Invalid temperature provided: [temperature]"
	}
	# Supported substitutions: [count], [promptLength]
	MAX_CHARACTERS_TOO_SMALL: dict[SupportedLanguages, str] = {
		"English": "Maximum input characters is too small to pass any user prompts ([count] vs. [promptLength] characters excluding context)."
	}
	# Supported substitutions: [error]
	QUERY_ERROR: dict[SupportedLanguages, str] = {
		"English": "Error generating response: [error]"
	}

# cache.py
class CacheTexts:
	# Supported substitutions: [time]
	INVALID_EXPIRATION_TIME: dict[SupportedLanguages, str] = {
		"English": "Invalid expiration time provided: [time]"
	}
	# Supported substitutions: [key]
	INVALID_KEY: dict[SupportedLanguages, str] = {
		"English": "Invalid key provided: [key]"
	}
	# Supported substitutions: [size]
	INVALID_MAX_SIZE: dict[SupportedLanguages, str] = {
		"English": "Invalid maximum cache size provided: [size]"
	}
	# Supported substitutions: [temperature]
	INVALID_SIMILARITY_THRESHOLD: dict[SupportedLanguages, str] = {
		"English": "Invalid minimum semantic similarity provided: [threshold]"
	}
	# Supported substitutions: [value]
	INVALID_VALUE: dict[SupportedLanguages, str] = {
		"English": "Invalid value provided: [value]"
	}

# Main.py
class MainTexts:
	NO_ARGUMENTS_FOUND: dict[SupportedLanguages, str] = {
		"English": "No arguments found when launching the chatbot.",
	}
	NO_DISCORD_BOT_TOKEN: dict[SupportedLanguages, str] = {
		"English": "No Discord bot token provided (must be 1st argument).",
	}

# messages.py
class MessagesTexts:
	ADD__SINGLE_WORDS_ONLY: dict[SupportedLanguages, str] = {
		"English": "All texts received solely consist of individual words. Make sure to wrap your texts in quotation marks.",
	}
	# Supported substitutions: [count], [plural]
	ADD__ERROR: dict[SupportedLanguages, str] = {
		"English": "[count] object[plural] failed to be added."
	}
	ASK__AI_DISCLAIMER: dict[SupportedLanguages, str] = {
		"English": "My response was AI-generated and therefore may contain errors and inaccuracies. Verify all information before using anything."
	}
	ASK__CACHED_RESPONSE: dict[SupportedLanguages, str] = {
		"English": "Cached response.",
	}
	# Supported substitutions: [seconds]
	ASK__COOLDOWN: dict[SupportedLanguages, str] = {
		"English": "I am currently on cooldown: too many queries are being made right now. ([seconds] seconds remaining)",
	}
	ASK__DEFAULT_CONTEXT: dict[SupportedLanguages, str] = {
		"English": "None",
	}
	ASK__ERROR_IF_NO_CONTEXT: dict[SupportedLanguages, str] = {
		"English": "No sources could be found that relate to the provided query."
	}
	# Supported substitutions: [messages]
	ASK__RETURN_VECTORSTORE: dict[SupportedLanguages, str] = {
		"English": """Here are the messages in my corpus most likely to be relevant to your question:
[messages]""",
	}
	BLOCKED: dict[SupportedLanguages, str] = {
		"English": f"`You are blocked from interacting with this bot.",
	}
	# Supported substitutions: [descriptions], [emote]
	HELP: dict[SupportedLanguages, str] = {
		"English": """Hi! I'm a chatbot designed to answer basic questions about whatever corpus I was given.
**I am still under development and do not have full functionality yet.**

I'm primarily interacted with via pinging me or slash commands. The commands I support are
[descriptions]

For messages sent after I'm added, trusted users can also request to add existing messages to the vectorstore by reacting with [emote], assuming the original author then gives his/her permission."""
	}
	IS_IN__FOUND_EMOTES: dict[SupportedLanguages, Iterable[str]] = {
		"English": ("🇾", "🇪", "🇸")
	}
	IS_IN__NOT_FOUND_EMOTES: dict[SupportedLanguages, Iterable[str]] = {
		"English": ("🇳", "🇴")
	}
	LOAD__ERROR: dict[SupportedLanguages, str] = {
		"English": "An error occurred while loading the object.",
	}
	# Supported substitutions: [command]
	NOT_OWNER: dict[SupportedLanguages, str] = {
		"English": f"`[command]` is an owner-only command.",
	}
	# Supported substitutions: [command]
	NOT_TRUSTED: dict[SupportedLanguages, str] = {
		"English": f"`[command]` is a trusted-only command.",
	}
	# Supported substitutions: [latency]
	PING: dict[SupportedLanguages, str] = {
		"English": "My latency is [latency] seconds.",
	}
	REMOVE__SINGLE_WORDS_ONLY: dict[SupportedLanguages, str] = {
		"English": "All texts received solely consist of individual words. Make sure to wrap your texts in quotation marks.",
	}
	# Supported substitutions: [count], [plural]
	REMOVE__ERROR: dict[SupportedLanguages, str] = {
		"English": "[count] object[plural] failed to be removed."
	}
	SAVE__ERROR: dict[SupportedLanguages, str] = {
		"English": "An error occurred while saving the object.",
	}

class RequestsTexts:
	# Supported substitutions: [missing]
	MISSING_KEYWORDS: dict[SupportedLanguages, str] = {
		"English": "Some provided keywords could not be found in provided message: [missing]"
	}
	PERMISSION_REQUEST: dict[SupportedLanguages, str] = {
		"English": """[recipientID], if you react to this message with ✅, this bot's trusted users will no longer need to request your permission to add your messages to the bot's corpus. This does not mean your messages WILL be added, but that they COULD be added if a trusted user thinks one of your messages would improve the bot.
This is entirely voluntary and can be revoked at any time by running `revoke`. However (for the moment at least), any messages of yours added prior to revocation will still remain in the bot's corpus, and will influence answers in all servers the bot is present in, not just this server.

To agree to this, react to this message with ✅. To reject this, react with ❌."""
	}
	RECIPIENT_ID_UNCHANGEABLE: dict[SupportedLanguages, str] = {
		"English": "Recipient ID cannot be changed."
	}
	RECIPIENT_ID_MUST_EXIST: dict[SupportedLanguages, str] = {
		"English": "Recipient ID cannot be recorded as None."
	}
	# Supported substitutions: [recipientID], [requesterIDs], [desiredMessageLinks]
	VECTORSTORE_REQUEST: dict[SupportedLanguages, str] = {
		"English": """Hi [recipientID]. [requesterIDs] would like to add the following messages of yours to this bot's corpus.
[desiredMessageLinks]
If you allow this, the information in those messages may be incorporated into future answers the bot provides, whenever it is asked relevant questions. This is entirely voluntary, but (for the moment at least) it cannot be undone, and it will influence answers in all servers the bot is present in, not just this server.

To agree to this, react to this message with ✅. To reject this, react with ❌.
-# If more of your messages are requested to be added before this message is answered, this message will be updated instead of a new message being generated."""
	}